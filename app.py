from flask import Flask, render_template, request, redirect, url_for, session    
from database.mongodb import users_collection, notes_collection, feedback_collection
import bcrypt
import json
from datetime import date, timedelta
from bson.objectid import ObjectId
import random
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

@app.context_processor
def inject_theme():
    if "user_email" not in session:
        return {"current_theme": "classic"}

    user = users_collection.find_one({"email": session["user_email"]})

    if not user:
        return {"current_theme": "classic"}

    return {
        "current_theme": user.get("theme", "classic")
    }

def get_user_language(user):
    return user.get("language", "marathi")


def load_lessons_for_user(user):
    language = get_user_language(user)
    theme = user.get("theme", "classic")

    if theme == "relationship":
        file_path = f"data/languages/{language}/relationship_lessons.json"
    else:
        file_path = f"data/languages/{language}/lessons.json"

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(file)

    # Classic lessons.json is usually a list.
    # relationship_lessons.json may be {"lessons": []}.
    if isinstance(data, dict):
        return data.get("lessons", [])

    return data


def load_interest_lessons_for_user(user):
    language = get_user_language(user)

    with open(
        f"data/languages/{language}/interest_lessons.json",
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)

def calculate_level(xp):
    if xp >= 350:
        return 5
    elif xp >= 200:
        return 4
    elif xp >= 100:
        return 3
    elif xp >= 50:
        return 2
    else:
        return 1
    
def get_level_title(xp):
    level = calculate_level(xp)

    titles = {
        1: "Tiny Capybara 🦫",
        2: "Curious Explorer 🌱",
        3: "Language Adventurer 🧭",
        4: "Confident Speaker 💬",
        5: "Fluent Beaver 👑"
    }

    return titles.get(level, "Language Legend 🏆")

def get_daily_challenge():
    return {
        "title": "Complete 1 lesson today",
        "reward_xp": 15
    }

def get_word_of_the_day(user):
    lessons = load_lessons_for_user(user)
    if not lessons:
        return None

    all_words = []

    for lesson in lessons:
        for word in lesson["words"]:
            all_words.append(word)

    if not all_words:
        return None

    today_index = date.today().toordinal() % len(all_words)

    return all_words[today_index]

def calculate_achievements(user):
    achievements = set(user.get("achievements", []))

    xp = user.get("xp", 0)
    streak = user.get("streak", 0)
    completed_lessons = user.get("completed_lessons", [])
    completed_interest_practices = user.get("completed_interest_practices", [])
    learned_words = user.get("learned_words", [])

    if len(completed_lessons) >= 1:
        achievements.add("🌱 First Lesson Completed")

    if len(completed_lessons) >= 10:
        achievements.add("📚 10 Lessons Completed")

    if len(completed_lessons) >= 25:
        achievements.add("📘 25 Lessons Completed")

    if len(completed_lessons) >= 50:
        achievements.add("🏆 50 Lessons Completed")

    if xp >= 50:
        achievements.add("⭐ 50 XP Earned")

    if xp >= 100:
        achievements.add("🌟 100 XP Earned")

    if xp >= 250:
        achievements.add("💫 250 XP Earned")

    if xp >= 500:
        achievements.add("🚀 500 XP Earned")

    if streak >= 3:
        achievements.add("🔥 3 Day Streak")

    if streak >= 7:
        achievements.add("🔥 7 Day Streak")

    if streak >= 30:
        achievements.add("👑 30 Day Streak")

    if len(learned_words) >= 25:
        achievements.add("🧠 25 Words Learned")

    if len(learned_words) >= 50:
        achievements.add("📖 50 Words Learned")

    if len(completed_interest_practices) >= 1:
        achievements.add("💛 First Personalized Practice")

    if len(completed_interest_practices) >= 5:
        achievements.add("🎯 5 Personalized Practices")

    return list(achievements)

def get_all_achievements():
    return [
        "🌱 First Lesson Completed",
        "📚 10 Lessons Completed",
        "📘 25 Lessons Completed",
        "🏆 50 Lessons Completed",
        "⭐ 50 XP Earned",
        "🌟 100 XP Earned",
        "💫 250 XP Earned",
        "🚀 500 XP Earned",
        "🔥 3 Day Streak",
        "🔥 7 Day Streak",
        "👑 30 Day Streak",
        "🧠 25 Words Learned",
        "📖 50 Words Learned",
        "💛 First Personalized Practice",
        "🎯 5 Personalized Practices"
    ]

def update_user_achievements(email):
    user = users_collection.find_one({"email": email})

    if not user:
        return

    achievements = calculate_achievements(user)

    users_collection.update_one(
        {"email": email},
        {
            "$set": {
                "achievements": achievements
            }
        }
    )

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if len(password) < 8:
            return "Password must be at least 8 characters long."

        if not any(char.isdigit() for char in password):
            return "Password must contain at least one number."

        existing_user = users_collection.find_one({"email": email})

        if existing_user:
            return "User already exists!"

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "language": "marathi",
            "streak": 0,
            "xp": 0,
            "interests": [],
            "completed_lessons": [],
            "current_lesson": 1,
            "achievements": [],
            "longest_streak": 0,
            "theme": "classic"
        }

        users_collection.insert_one(user)

        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = users_collection.find_one({"email": email})

        if user and bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            session["user_email"] = user["email"]
            session["username"] = user["username"]
            if not user.get("interests"):
                return redirect(url_for("interests"))

            return redirect(url_for("dashboard"))

        return "Invalid email or password"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})

    level = calculate_level(user.get("xp", 0))
    level_title = get_level_title(user.get("xp", 0))

    xp = user.get("xp", 0)
    xp_for_next_level = level * 50
    xp_progress = xp % 50

    lessons = load_lessons_for_user(user)
    interest_lessons = load_interest_lessons_for_user(user)

    user_interests = user.get("interests", [])
    personalized_lesson = None

    for interest in user_interests:
        lessons_for_interest = interest_lessons.get(interest, [])
        if lessons_for_interest:
            personalized_lesson = lessons_for_interest[0]
            break

    completed_lessons = user.get("completed_lessons", [])

    today = date.today().isoformat()
    last_completed_date = user.get("last_completed_date")

    lesson_goal_done = last_completed_date == today
    quiz_goal_done = user.get("last_daily_quiz_completed") == today
    revision_goal_done = user.get("last_revision_completed") == today

    daily_goals = [
        {
            "title": "Complete 1 lesson",
            "done": lesson_goal_done,
            "icon": "📚"
        },
        {
            "title": "Take daily quiz",
            "done": quiz_goal_done,
            "icon": "🎯"
        },
        {
            "title": "Revise vocabulary",
            "done": revision_goal_done,
            "icon": "🧠"
        }
    ]

    daily_goals_done_count = sum(1 for goal in daily_goals if goal["done"])
    daily_goals_total = len(daily_goals)

    daily_goal_done = last_completed_date == today
    daily_challenge = get_daily_challenge()

    completed_count = len(completed_lessons)
    total_lessons = len(lessons)

    if total_lessons > 0:
        progress_percentage = int((completed_count / total_lessons) * 100)
    else:
        progress_percentage = 0

    next_lesson = None

    for lesson_item in lessons:
        if lesson_item["id"] not in completed_lessons:
            next_lesson = lesson_item
            break

    word_of_the_day = get_word_of_the_day(user)

    if user.get("streak", 0) >= 7:
        mascot = "capybara-excited.png"
    elif user.get("streak", 0) >= 3:
        mascot = "capybara-happy.png"
    else:
        mascot = "capybara-welcome.png"

    all_achievements = get_all_achievements()
    unlocked_achievements = user.get("achievements", [])
    latest_achievement = unlocked_achievements[-1] if unlocked_achievements else None
    achievement_count = len(unlocked_achievements)
    total_achievement_count = len(all_achievements)

    return render_template(
        "dashboard.html",
        username=user["username"],
        xp=user.get("xp", 0),
        streak=user.get("streak", 0),
        next_lesson=next_lesson,
        completed_count=completed_count,
        total_lessons=total_lessons,
        progress_percentage=progress_percentage,
        achievements=user.get("achievements", []),
        daily_goal_done=daily_goal_done,
        interests=user.get("interests", []),
        personalized_lesson=personalized_lesson,
        level=level,
        xp_for_next_level=xp_for_next_level,
        xp_progress=xp_progress,
        daily_challenge=daily_challenge,
        longest_streak=user.get("longest_streak", 0),
        word_of_the_day=word_of_the_day,
        mascot=mascot,
        user_language=user.get("language", "marathi").title(),
        daily_goals=daily_goals,
        daily_goals_done_count=daily_goals_done_count,
        daily_goals_total=daily_goals_total,
        level_title=level_title,
        latest_achievement=latest_achievement,
        achievement_count=achievement_count,
        total_achievement_count=total_achievement_count,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/lesson/<int:lesson_id>")
def lesson(lesson_id):
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})
    lessons = load_lessons_for_user(user)
    if not lessons:
        return render_template("relationship_coming_soon.html")

    selected_lesson = None

    for lesson_item in lessons:
        if lesson_item["id"] == lesson_id:
            selected_lesson = lesson_item
            break

    if selected_lesson is None:
        return "Lesson not found"

    user_notes = list(notes_collection.find({
    "email": session["user_email"],
    "lesson_id": str(lesson_id)
    }))
    return render_template("lesson.html", lesson=selected_lesson, user_notes=user_notes)

@app.route("/interests", methods=["GET", "POST"])
def interests():
    if "user_email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        selected_interests = request.form.getlist("interests")

        users_collection.update_one(
            {"email": session["user_email"]},
            {"$set": {"interests": selected_interests}}
        )

        return redirect(url_for("dashboard"))

    return render_template("interests.html")

@app.route("/save-note", methods=["POST"])
def save_note():
    if "user_email" not in session:
        return redirect(url_for("login"))

    lesson_id = request.form.get("lesson_id")
    note_text = request.form.get("note")

    note = {
        "email": session["user_email"],
        "lesson_id": lesson_id,
        "note": note_text
    }

    notes_collection.insert_one(note)

    return redirect(url_for("lesson", lesson_id=lesson_id))

@app.route("/notes")
def notes():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user_notes = list(notes_collection.find({
        "email": session["user_email"]
    }))

    return render_template("notes.html", user_notes=user_notes)

@app.route("/complete-lesson/<int:lesson_id>")
def complete_lesson(lesson_id):
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})

    lessons = load_lessons_for_user(user)

    if not lessons:
        return render_template("relationship_coming_soon.html")

    if not any(lesson["id"] == lesson_id for lesson in lessons):
        return "Lesson not found"

    completed_lessons = user.get("completed_lessons", [])

    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    last_completed_date = user.get("last_completed_date")

    current_streak = user.get("streak", 0)
    longest_streak = user.get("longest_streak", 0)

    bonus_xp = 0

    if lesson_id not in completed_lessons:

        if user.get("last_daily_challenge_claimed") != today:
            bonus_xp = 15

        update_data = {
            "$addToSet": {
                "completed_lessons": lesson_id,
                "practice_dates": today
            },
            "$inc": {
                "xp": 10 + bonus_xp
            },
            "$set": {
                "last_daily_challenge_claimed": today
            }
        }

        if last_completed_date == today:
            pass

        elif last_completed_date == yesterday:
            new_streak = current_streak + 1

            update_data["$inc"]["streak"] = 1
            update_data["$set"]["last_completed_date"] = today
            update_data["$set"]["longest_streak"] = max(longest_streak, new_streak)

        else:
            update_data["$set"]["streak"] = 1
            update_data["$set"]["last_completed_date"] = today
            update_data["$set"]["longest_streak"] = max(longest_streak, 1)

        users_collection.update_one(
            {"email": session["user_email"]},
            update_data
        )
        update_user_achievements(session["user_email"])

    return redirect(url_for("lesson_complete", lesson_id=lesson_id, bonus_xp=bonus_xp))


@app.route("/lesson-complete/<int:lesson_id>")
def lesson_complete(lesson_id):
    if "user_email" not in session:
        return redirect(url_for("login"))

    bonus_xp = request.args.get("bonus_xp", 0, type=int)

    return render_template(
        "lesson_complete.html",
        lesson_id=lesson_id,
        bonus_xp=bonus_xp
    )

@app.route("/profile")
def profile():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})

    level_title = get_level_title(user.get("xp", 0))

    return render_template(
        "profile.html",
        user=user,
        level_title=level_title
    )

@app.route("/edit-interests", methods=["GET", "POST"])
def edit_interests():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})

    if request.method == "POST":
        selected_interests = request.form.getlist("interests")

        users_collection.update_one(
            {"email": session["user_email"]},
            {"$set": {"interests": selected_interests}}
        )

        return redirect(url_for("profile"))

    return render_template("edit_interests.html", user=user)

@app.route("/vocabulary")
def vocabulary():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})
    completed_lessons = user.get("completed_lessons", [])

    lessons = load_lessons_for_user(user)

    learned_words = []

    for lesson_item in lessons:
        if lesson_item["id"] in completed_lessons:
            for word in lesson_item["words"]:
                learned_words.append({
                    "lesson_id": lesson_item["id"],
                    "word": word.get("word"),
                    "transliteration": word.get("transliteration", ""),
                    "meaning": word.get("meaning")
                })

    return render_template("vocabulary.html", learned_words=learned_words)


@app.route("/review")
def review():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})
    completed_lessons = user.get("completed_lessons", [])

    lessons = load_lessons_for_user(user)
    if not lessons:
        return render_template("relationship_coming_soon.html")

    completed_lesson_data = []

    for lesson_item in lessons:
        if lesson_item["id"] in completed_lessons:
            completed_lesson_data.append(lesson_item)

    return render_template("review.html", completed_lesson_data=completed_lesson_data)

@app.route("/personalized-practice")
def personalized_practice():

    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({
        "email": session["user_email"]
    })

    return render_template(
        "personalized_practice.html",
        interests=user.get("interests", [])
    )

@app.route("/interest/<interest_name>")
def interest_lesson(interest_name):

    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})

    interest_lessons = load_interest_lessons_for_user(user)

    lessons = interest_lessons.get(interest_name, [])

    if not lessons:
        return "No lessons available yet."

    completed = user.get("completed_interest_practices", [])

    next_lesson = None

    for lesson in lessons:
        lesson_key = f"{interest_name}-{lesson['id']}"
        if lesson_key not in completed:
            next_lesson = lesson
            break

    if next_lesson is None:
        next_lesson = lessons[0]

    return render_template(
        "interest_lesson.html",
        lesson=next_lesson,
        interest=interest_name
    )

@app.route("/complete-interest/<interest_name>/<int:lesson_id>")
def complete_interest(interest_name, lesson_id):

    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})

    completed_interest_practices = user.get(
        "completed_interest_practices",
        []
    )

    today = date.today().isoformat()

    lesson_key = f"{interest_name}-{lesson_id}"

    if lesson_key not in completed_interest_practices:

        update_data = {
            "$addToSet": {
                "completed_interest_practices": lesson_key,
                "practice_dates": today
            },
            "$inc": {
                "xp": 5
            }
        }

        users_collection.update_one(
            {"email": session["user_email"]},
            update_data
        )

        update_user_achievements(session["user_email"])

    return redirect(url_for("interest_lesson", interest_name=interest_name))

@app.route("/leaderboard")
def leaderboard():
    if "user_email" not in session:
        return redirect(url_for("login"))

    current_email = session["user_email"]

    users = list(users_collection.find().sort("xp", -1))

    for index, user in enumerate(users):
        user["rank"] = index + 1
        user["level"] = calculate_level(user.get("xp", 0))
        user["level_title"] = get_level_title(user.get("xp", 0))
        user["is_current_user"] = user.get("email") == current_email

    return render_template("leaderboard.html", users=users)

@app.route("/flashcards")
def flashcards():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({
        "email": session["user_email"]
    })

    completed_lessons = user.get("completed_lessons", [])

    lessons = load_lessons_for_user(user)

    flashcards = []

    if lessons:
        for lesson in lessons:
            if lesson["id"] in completed_lessons:
                for word in lesson["words"]:
                    flashcards.append(word)

    return render_template(
        "flashcards.html",
        flashcards=flashcards
    )

@app.route("/revision")
def revision():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})
    completed_lessons = user.get("completed_lessons", [])

    lessons = load_lessons_for_user(user)
    if not lessons:
        return render_template("relationship_coming_soon.html")

    revision_words = []

    for lesson in lessons:
        if lesson["id"] in completed_lessons:
            for word in lesson["words"]:
                revision_words.append(word)

    return render_template("revision.html", revision_words=revision_words)

@app.route("/stats")
def stats():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})

    lessons = load_lessons_for_user(user)
    completed_lessons = user.get("completed_lessons", [])

    total_lessons = len(lessons)
    completed_count = len(completed_lessons)

    words_learned = 0

    for lesson in lessons:
        if lesson["id"] in completed_lessons:
            words_learned += len(lesson["words"])

    progress_percentage = round(
        (completed_count / total_lessons) * 100
    ) if total_lessons > 0 else 0

    return render_template(
        "stats.html",
        user=user,
        total_lessons=total_lessons,
        completed_count=completed_count,
        words_learned=words_learned,
        progress_percentage=progress_percentage
    )


@app.route("/delete-note/<note_id>")
def delete_note(note_id):
    if "user_email" not in session:
        return redirect(url_for("login"))

    notes_collection.delete_one({
        "_id": ObjectId(note_id),
        "email": session["user_email"]
    })

    return redirect(url_for("notes"))

@app.route("/edit-note/<note_id>", methods=["GET", "POST"])
def edit_note(note_id):
    if "user_email" not in session:
        return redirect(url_for("login"))

    note = notes_collection.find_one({
        "_id": ObjectId(note_id),
        "email": session["user_email"]
    })

    if note is None:
        return "Note not found"

    if request.method == "POST":
        updated_note = request.form.get("note")

        notes_collection.update_one(
            {
                "_id": ObjectId(note_id),
                "email": session["user_email"]
            },
            {
                "$set": {
                    "note": updated_note
                }
            }
        )

        return redirect(url_for("notes"))

    return render_template("edit_note.html", note=note)

@app.route("/add-note", methods=["GET", "POST"])
def add_note():
    if "user_email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title")
        note_text = request.form.get("note")

        note = {
            "email": session["user_email"],
            "lesson_id": "general",
            "title": title,
            "note": note_text
        }

        notes_collection.insert_one(note)

        return redirect(url_for("notes"))

    return render_template("add_note.html")

@app.route("/daily-quiz")
def daily_quiz():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})
    today = date.today().isoformat()

    if user.get("last_daily_quiz_completed") == today:
        return render_template(
            "daily_quiz_result.html",
            is_correct=True,
            already_completed=True,
            correct_answer=None,
            selected_answer=None,
            xp_awarded=0
        )

    completed_lessons = user.get("completed_lessons", [])

    lessons = load_lessons_for_user(user)
    if not lessons:
        return render_template("relationship_coming_soon.html")

    learned_words = []

    for lesson in lessons:
        if lesson["id"] in completed_lessons:
            for word in lesson["words"]:
                learned_words.append(word)

    if not learned_words:
        return "Complete a lesson first to unlock daily quiz."

    today_index = date.today().toordinal() % len(learned_words)
    quiz_word = learned_words[today_index]

    options = [quiz_word["meaning"]]

    for word in learned_words:
        if word["meaning"] not in options:
            options.append(word["meaning"])
        if len(options) == 4:
            break

    random.shuffle(options)

    return render_template(
        "daily_quiz.html",
        quiz_word=quiz_word,
        options=options
    )


@app.route("/check-daily-quiz", methods=["POST"])
def check_daily_quiz():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})
    today = date.today().isoformat()

    if user.get("last_daily_quiz_completed") == today:
        return render_template(
            "daily_quiz_result.html",
            is_correct=True,
            already_completed=True,
            correct_answer=None,
            selected_answer=None,
            xp_awarded=0
        )

    selected_answer = request.form.get("answer")
    correct_answer = request.form.get("correct_answer")

    if selected_answer == correct_answer:
        users_collection.update_one(
            {"email": session["user_email"]},
            {
                "$inc": {"xp": 5},
                "$set": {"last_daily_quiz_completed": today},
                "$addToSet": {"practice_dates": today}
            }
        )
        update_user_achievements(session["user_email"])

        return render_template(
            "daily_quiz_result.html",
            is_correct=True,
            already_completed=False,
            correct_answer=correct_answer,
            selected_answer=selected_answer,
            xp_awarded=5
        )

    return render_template(
        "daily_quiz_result.html",
        is_correct=False,
        already_completed=False,
        correct_answer=correct_answer,
        selected_answer=selected_answer,
        xp_awarded=0
    )

@app.route("/change-language", methods=["GET", "POST"])
def change_language():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})

    available_languages = [
        {
            "code": "marathi",
            "name": "Marathi",
            "status": "available"
        },
        {
            "code": "hindi",
            "name": "Hindi",
            "status": "coming_soon"
        },
        {
            "code": "spanish",
            "name": "Spanish",
            "status": "coming_soon"
        }
    ]

    if request.method == "POST":
        selected_language = request.form.get("language")

        if selected_language != "marathi":
            return "This language is coming soon."

        users_collection.update_one(
            {"email": session["user_email"]},
            {
                "$set": {
                    "language": selected_language,
                    "completed_lessons": [],
                    "completed_interest_practices": [],
                    "learned_words": []
                }
            }
        )

        return redirect(url_for("dashboard"))

    return render_template(
        "change_language.html",
        user=user,
        available_languages=available_languages
    )

@app.template_filter("shuffle")
def shuffle_filter(items):
    items = list(items)
    random.shuffle(items)
    return items

@app.route("/settings")
def settings():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})

    return render_template("settings.html", user=user)

@app.route("/complete-revision")
def complete_revision():
    if "user_email" not in session:
        return redirect(url_for("login"))

    today = date.today().isoformat()

    users_collection.update_one(
        {"email": session["user_email"]},
        {
            "$set": {
                "last_revision_completed": today
            },
            "$addToSet": {
                "practice_dates": today
            }
        }
    )

    update_user_achievements(session["user_email"])

    return redirect(url_for("dashboard"))

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})

    if request.method == "POST":
        feedback_type = request.form.get("feedback_type")
        message = request.form.get("message")
        phrase = request.form.get("phrase")
        language = request.form.get("language")

        if not message:
            return "Please write your feedback."

        feedback_data = {
            "email": session["user_email"],
            "username": user.get("username"),
            "feedback_type": feedback_type,
            "message": message,
            "phrase": phrase,
            "language": language,
            "created_at": date.today().isoformat()
        }

        feedback_collection.insert_one(feedback_data)

        return render_template("feedback_success.html")

    return render_template("feedback.html", user=user)

@app.route("/theme-settings")
def theme_settings():
    if "user_email" not in session:
        return redirect(url_for("login"))

    user = users_collection.find_one({"email": session["user_email"]})
    current_theme = user.get("theme", "classic")

    return render_template(
        "theme_settings.html",
        current_theme=current_theme
    )


@app.route("/change-theme", methods=["POST"])
def change_theme():
    if "user_email" not in session:
        return redirect(url_for("login"))

    selected_theme = request.form.get("theme")

    if selected_theme not in ["classic", "relationship"]:
        return "Invalid theme selected"

    users_collection.update_one(
        {"email": session["user_email"]},
        {"$set": {"theme": selected_theme}}
    )

    return redirect(url_for("theme_settings"))

if __name__ == "__main__":
    app.run(debug=True)