from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from forms import SignUpForm, LoginForm, NewListForm, NewTaskForm
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv("./.env")
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
# create/connect to database
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL").replace("://", "ql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///cuddley.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)

    # one-to-many relationship from User to List
    lists = relationship("List", back_populates="list_creator")

    # one-to-many relationship from User to Task
    tasks = relationship("Task", back_populates="task_creator")


class List(db.Model):
    __tablename__ = "lists"
    id = db.Column(db.Integer, primary_key=True)
    list_name = db.Column(db.String, nullable=False)

    # one-to-many relationship from List to Task
    tasks = relationship("Task", back_populates="parent_list")

    # child relationship with User - creating a foreign key on the child table lists that references the parent, users
    # foreign key is placed under the new field list_creator_id
    # "users.id" The users refers to the tablename of the Users class.
    list_creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))  # adds new column in List for foreign key
    list_creator = relationship("User", back_populates="lists")

    #  return a printable representational string of the given object
    def __repr__(self):
        return self.list_name


class Task (db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String, nullable=False)
    task_description = db.Column(db.String)
    deadline = db.Column(db.String(50))
    progress = db.Column(db.Boolean, nullable=False)
    date_created = db.Column(db.Date, nullable=False)

    # child relationship with User - creating a foreign key on the child table tasks that references the parent, users
    # foreign key is placed under the new field list_creator_id
    # "users.id" The users refers to the tablename of the Users class.
    task_creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))  # adds new column in Task for foreign key
    task_creator = relationship("User", back_populates="tasks")

    # child relationship with List - creating a foreign key on the child table tasks that references the parent, lists
    # foreign key is placed under the new field list_creator_id
    # "lists.id" The users refers to the tablename of the List class.
    parent_list_id = db.Column(db.Integer, db.ForeignKey("lists.id"))  # adds new column in Task for foreign key
    parent_list = relationship("List", back_populates="tasks")


db.create_all()

CURRENT_YEAR = datetime.now().year

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard", username=current_user.username))
    return render_template("index.html", current_user=current_user, current_year=CURRENT_YEAR)


@app.route('/sign-up', methods=["GET", "POST"])
def sign_up():
    sign_up_form = SignUpForm()
    if sign_up_form.validate_on_submit():
        if User.query.filter_by(email=sign_up_form.email.data).first():
            flash("Sorry, this email has already been registered. Please log in instead.")
            return redirect(url_for("login"))
        new_user = User()
        new_user.username = sign_up_form.username.data
        new_user.password = generate_password_hash(sign_up_form.password.data, method="pbkdf2:sha256", salt_length=8)
        new_user.email = sign_up_form.email.data
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("dashboard", username=current_user.username))
    return render_template("signup.html", form=sign_up_form, current_user=current_user,
                           current_year=CURRENT_YEAR)


@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        login_email = login_form.email.data
        login_password = login_form.password.data
        requested_user = User.query.filter_by(email=login_email).first()
        if requested_user:
            if check_password_hash(pwhash=requested_user.password, password=login_password):
                login_user(requested_user)
                return redirect(url_for("dashboard", username=current_user.username))
            else:
                flash("Sorry, wrong password! Please try again.")
                return redirect(url_for("login"))
        else:
            flash("Sorry, that email does not exist! Please try again.")
            return redirect(url_for("login"))
    return render_template("login.html", form=login_form, current_user=current_user,
                           current_year=CURRENT_YEAR)


@app.route('/new-list', methods=["GET", "POST"])
@login_required
def new_list():
    list_form = NewListForm()
    if list_form.validate_on_submit():
        new_list_name = list_form.list_name.data
        if List.query.filter_by(list_name=new_list_name, list_creator_id=current_user.id).first():
            flash("Sorry! You already have a list with this name. Please enter another one.")
            return redirect(url_for("new_list"))
        list_to_add = List()
        list_to_add.list_name = new_list_name
        list_to_add.list_creator_id = current_user.id
        db.session.add(list_to_add)  # add list
        db.session.commit()
        # add default task
        default_task = Task(task_name="New Task",
                            task_description="Task description/details",
                            deadline=datetime.now().strftime('%B %d, %Y at %I:%M%p'),
                            progress=False,
                            date_created=datetime.now().date(),
                            task_creator_id=current_user.id,
                            parent_list_id=list_to_add.id)
        db.session.add(default_task)
        db.session.commit()
        return redirect(url_for("dashboard", username=current_user.username))
    return render_template("add-list.html", form=list_form, operation="Add", current_user=current_user,
                           current_year=CURRENT_YEAR)


@app.route('/update-list/<int:list_id>', methods=["GET", "POST"])
@login_required
def update_list(list_id):
    list_to_edit = List.query.get(list_id)
    edit_form = NewListForm(
        list_name=list_to_edit.list_name
    )
    if edit_form.validate_on_submit():
        new_list_name = edit_form.list_name.data
        if List.query.filter_by(list_name=new_list_name, id=current_user.id).first():
            flash("Sorry! You already have a list with this name. Please enter another one.")
            return redirect(url_for("update_list", list_id=list_id))
        list_to_edit.list_name = new_list_name
        db.session.commit()
        return redirect(url_for("dashboard", username=current_user.username))
    return render_template("add-list.html", form=edit_form, operation="Edit", current_user=current_user,
                           current_year=CURRENT_YEAR)


@app.route('/delete-list/<int:list_id>')
@login_required
def delete_list(list_id):
    list_to_delete = List.query.get(list_id)
    all_user_tasks = Task.query.filter_by(task_creator_id=current_user.id).all()
    for task in all_user_tasks:
        if task.parent_list_id == list_to_delete.id:
            db.session.delete(task)
            db.session.commit()
    # current_user.lists.remove(list_to_delete)
    db.session.delete(list_to_delete)
    db.session.commit()
    return redirect(url_for("dashboard", username=current_user.username))


@app.route('/new-task/<int:list_id>', methods=["GET", "POST"])
@login_required
def new_task(list_id):
    task_form = NewTaskForm()
    # task_form.parent_list.choices = [lst for lst in current_user.lists]
    task_form.parent_list.choices = [List.query.filter_by(id=list_id).first()]
    if task_form.validate_on_submit():
        # print(task_form.deadline)
        # print(type(task_form.deadline)
        # parent_list = List.query.filter_by(list_name=task_form.parent_list.data).first()
        parent_list = List.query.filter_by(id=list_id).first()
        task_to_add = Task(
            task_name=task_form.task_name.data,
            task_description=task_form.description.data,
            deadline=task_form.deadline.data,
            progress=False,
            date_created=datetime.now().date(),
            task_creator_id=current_user.id,
            parent_list_id=parent_list.id)
        db.session.add(task_to_add)
        db.session.commit()
        return redirect(url_for("dashboard", username=current_user.username))
    return render_template("add-task.html", form=task_form, operation="Add", current_user=current_user, current_year=CURRENT_YEAR)


@app.route('/update-task/<int:task_id>', methods=["GET", "POST"])
@login_required
def update_task(task_id):
    task_to_edit = Task.query.get(task_id)
    # print(type(task_to_edit.deadline))
    # datetime.strptime(task_to_edit.deadline.replace(" ", ","), "%Y-%m-%d,%I:%M%p") # convert string to datetime format
    edit_form = NewTaskForm(
        task_name=task_to_edit.task_name,
        description=task_to_edit.task_description,
        deadline=task_to_edit.deadline,
        parent_list=List.query.filter_by(id=task_to_edit.parent_list_id).first()
    )
    # edit_form.parent_list.choices = [lst for lst in current_user.lists]
    edit_form.parent_list.choices = [List.query.filter_by(id=task_to_edit.parent_list_id).first()]
    if edit_form.validate_on_submit():
        # parent_list = List.query.filter_by(list_name=edit_form.parent_list.data).first()
        # parent_list = List.query.filter_by(list_name=edit_form.parent_list.data).first()
        task_to_edit.task_name = edit_form.task_name.data
        task_to_edit.task_description = edit_form.description.data
        task_to_edit.deadline = edit_form.deadline.data
        # task_to_edit.parent_list_id = parent_list.id
        db.session.commit()
        return redirect(url_for("dashboard", username=current_user.username))
    return render_template("add-task.html", form=edit_form, operation="Edit", current_user=current_user, current_year=CURRENT_YEAR)


@app.route('/delete-task/<int:task_id>')
@login_required
def delete_task(task_id):
    task_to_delete = Task.query.get(task_id)
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect(url_for("dashboard", username=current_user.username))


@app.route('/update-task-progress/<int:task_id>')
@login_required
def update_task_progress(task_id):
    task_to_update = Task.query.get(task_id)
    if task_to_update.progress == 0:
        task_to_update.progress = 1
    else:
        task_to_update.progress = 0
    db.session.commit()
    return redirect(url_for("dashboard", username=current_user.username))


@app.route('/dashboard/<username>')
@login_required
def dashboard(username):
    # all_user_tasks = Task.query.filter_by(task_creator_id=current_user.id).order_by(Task.deadline.asc()).all()
    all_user_tasks = Task.query.filter_by(task_creator_id=current_user.id).all()
    print(all_user_tasks)
    user_lists = [lst for lst in List.query.all() if lst.list_creator_id == current_user.id]
    print(user_lists)
    num_lists = len(user_lists)
    num_tasks = len(all_user_tasks)
    num_tasks_completed = len([task for task in all_user_tasks if task.progress == 1])
    return render_template("dashboard.html", current_user=current_user, user_lists=user_lists,
                           user_tasks=all_user_tasks, username=username, current_year=CURRENT_YEAR,
                           num_lists=num_lists, num_tasks=num_tasks, num_completed=num_tasks_completed)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home", current_user=current_user))


if __name__ == "__main__":
    app.run(debug=True)