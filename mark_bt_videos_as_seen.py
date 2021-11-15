from pprint import pprint

import json
import requests
from requests.adapters import HTTPAdapter

s = requests.Session()

s.mount("https://", HTTPAdapter(max_retries=10))
s.cookies.set("sessionid", "enter_sessionid_here")
s.cookies.set("csrftoken", "enter_csrftoken_here")


def mark_video_as_seen(video_id, concept_id):
    video_data = s.get(
        f"https://pccoe.bodhi-tree.in/video/api/video/{video_id}/",
    ).json()

    video_title = video_data["title"]

    print(f"\nMarking video '{video_title}' as seen. ", end="")

    pprint(
        s.patch(
            f"https://pccoe.bodhi-tree.in/video/api/video/{video_id}/ended/",
            headers={
                "X-CSRFToken": "WMra8VOcXXlqkx1aGHKxXCbL3Do9CXJF",
                "referer": f"https://pccoe.bodhi-tree.in/concept/{concept_id}/",
            },
        ).json(),
    )


def main():
    courses = s.get(
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

        chapters = s.get(
            f"https://pccoe.bodhi-tree.in/courseware/api/course/{course_id}/groups/"
        ).json()

        for chapter in chapters:
            group_id = chapter["id"]

            print("=" * 100)
            print("Chapter:", chapter["title"])
            print("=" * 100)

            groups = s.get(
                f"https://pccoe.bodhi-tree.in/courseware/api/group/{group_id}/published_concepts/",
            ).json()

            for group in groups:
                concept_id = group["id"]
                response = s.get(
                    f"https://pccoe.bodhi-tree.in/concept/api/concept/{concept_id}/get_concept_page_data/",
                )
                concepts = response.json()["playlist"]
                for concept in concepts:
                    if concept["type"] == "video":
                        video_id = concept["content"]["id"]
                        mark_video_as_seen(video_id, concept_id)

    s.close()


main()
