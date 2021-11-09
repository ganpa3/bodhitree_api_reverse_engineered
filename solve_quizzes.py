import json
from pprint import pprint

import requests
from requests.adapters import HTTPAdapter

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.7113.93 Safari/537.36"

MY_SESSIONID = "mf1vclnej0npwfh37z6m4isuycqyu000"
MY_CSRF_TOKEN = "WMra8VOcXXlqkx1aGHKxXCbL3Do9CXJF"

MY_SESSION = requests.Session()
MY_SESSION.mount("https://", HTTPAdapter(max_retries=10))
MY_SESSION.cookies.set("sessionid", MY_SESSIONID)
MY_SESSION.cookies.set("csrftoken", MY_CSRF_TOKEN)
MY_SESSION.headers.update({"X-CSRFToken": MY_CSRF_TOKEN})
MY_SESSION.headers.update({"User-Agent": USER_AGENT})

OTHER_SESSION = requests.Session()
OTHER_SESSION.mount("https://", HTTPAdapter(max_retries=10))
OTHER_SESSION.cookies.set("sessionid", "u3gps5dwfdc0xr2gu1nrdh48jkcb484y")
OTHER_SESSION.headers.update({"User-Agent": USER_AGENT})
OTHER_SESSION.hooks["response"] = [
    lambda response, *args, **kwargs: response.raise_for_status()
]

SESSIONS = [OTHER_SESSION]


def submit_answer_for_mcq(mcq, mcq_answer, concept_id):
    mcq_id = mcq["id"]
    mcq_type = mcq["type"]
    mcq_options = mcq.get("options", "")
    mcq_options = json.loads(mcq_options) if mcq_options else ""
    mcq_question = mcq["description"]

    # Single choice MCQs
    if mcq_type == "S":
        answer = mcq_options.index(mcq_answer)
    # Multiple choice MCQs
    elif mcq_type == "M":
        answer = [False] * len(mcq_options)
        for i, choice in enumerate(mcq_options):
            if choice in mcq_answer:
                answer[i] = True
        answer = json.dumps(answer, separators=(",", ":"))
    # Subjective questions
    elif mcq_type == "F":
        answer = mcq_answer[0]
    else:
        answer = ""

    payload = {"answer": answer, "csrfmiddlewaretoken": MY_CSRF_TOKEN}

    print()
    print("=" * 100)
    print("Q:", mcq_question)
    print("Answer to be submitted:", answer)
    print("Actual answer:", mcq_answer)
    print("Options:", mcq_options)
    print("=" * 100)
    print("Continue?")

    confirm = input()
    if confirm == "y":
        response = MY_SESSION.post(
            f"https://pccoe.bodhi-tree.in/quiz/api/question/{mcq_id}/submit_answer/",
            data=payload,
            headers={
                "referer": f"https://pccoe.bodhi-tree.in/concept/{concept_id}/",
            },
        ).json()
        pprint(response, indent=4)


def get_answers_from_quiz_id(quiz_id, concept_id):
    question_modules = MY_SESSION.get(
        f"https://pccoe.bodhi-tree.in/quiz/api/quiz/{quiz_id}/get_published_question_modules/",
    ).json()

    for question_module in question_modules:
        question_id = question_module["id"]
        questions = MY_SESSION.get(
            f"https://pccoe.bodhi-tree.in/quiz/api/question_module/{question_id}/get_questions/",
        ).json()["questions"]
        questions = sorted(questions, key=lambda k: k["id"])

        others_questions = []
        for session in SESSIONS:
            tmp_question = session.get(
                f"https://pccoe.bodhi-tree.in/quiz/api/question_module/{question_id}/get_questions/",
            ).json()["questions"]
            others_questions.append(sorted(tmp_question, key=lambda k: k["id"]))

        for i, question in enumerate(questions):
            # Already solved
            if question["answer"]:
                continue

            actual_answer = None
            for others_question in others_questions:
                if others_question[i]["answer"]:
                    actual_answer = others_question[i]["answer"]

            if not actual_answer:
                continue

            submit_answer_for_mcq(question, actual_answer, concept_id)


# If is_out_video_quiz is true, video_id _is_ quiz_id
def get_answers_from_video(video_id, concept_id, is_out_video_quiz):
    if is_out_video_quiz:
        get_answers_from_quiz_id(video_id, concept_id)
    else:
        video_data = MY_SESSION.get(
            f"https://pccoe.bodhi-tree.in/video/api/video/{video_id}/",
        ).json()

        video_title = video_data["title"]

        does_quiz_exist = False
        for marker in video_data["markers"]:
            does_quiz_exist = "quiz" in marker

        if not does_quiz_exist:
            return

        print()
        print("/" * 100)
        print("Video:", video_title)
        print("/" * 100)
        print()

        for marker in video_data["markers"]:
            if "quiz" in marker:
                quiz_id = marker["quiz"]
                get_answers_from_quiz_id(quiz_id, concept_id)


def main():
    courses = MY_SESSION.get(
        "https://pccoe.bodhi-tree.in/courseware/student_courses_json/",
    ).json()["courses"]

    for course in json.loads(courses):
        course_id = course["id"]
        course_title = course["title"]

        print()
        print("*" * 100)
        print("Subject:", course_title)
        print("*" * 100)
        print()

        chapters = MY_SESSION.get(
            f"https://pccoe.bodhi-tree.in/courseware/api/course/{course_id}/groups/"
        ).json()

        for chapter in chapters:
            group_id = chapter["id"]

            print("=" * 100)
            print("Chapter:", chapter["title"])
            print("=" * 100)

            groups = MY_SESSION.get(
                f"https://pccoe.bodhi-tree.in/courseware/api/group/{group_id}/published_concepts/",
            ).json()

            for group in groups:
                concept_id = group["id"]
                response = MY_SESSION.get(
                    f"https://pccoe.bodhi-tree.in/concept/api/concept/{concept_id}/get_concept_page_data/",
                )

                concepts = response.json()["playlist"]
                for concept in concepts:
                    if concept["type"] == "document":
                        continue

                    video_id = concept["content"]["id"]
                    is_out_video_quiz = concept["type"] == "quiz"

                    get_answers_from_video(video_id, concept_id, is_out_video_quiz)


main()
