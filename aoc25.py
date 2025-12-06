import sys
import os
import requests
from google import genai
import subprocess


def get_environment():
    SESSION_KEY = os.getenv("AOC_SESSION")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not SESSION_KEY or not GEMINI_API_KEY:
        raise RuntimeError("Brak zmiennej środowiskowej!")
    return SESSION_KEY, GEMINI_API_KEY


def get_task_description_and_input(SESSION_KEY, year = 2025, day = 1):
    url_base = f"https://adventofcode.com/{year}/day/{day}"
    url_input = url_base + "/input"

    response_description = requests.get(url_base, cookies={"session": SESSION_KEY})
    response_input = requests.get(url_input, cookies={"session": SESSION_KEY})

    if response_description.status_code != 200 or response_input.status_code != 200:
        print("Błąd Description:", response_description.status_code)
        print("Błąd Input:", response_input.status_code)

        print(response_description.text)
        print(response_input.text)

        raise RuntimeError("Problem z zczytaniem danych")
    
    description = response_description.text
    input = response_input.text

    description = description[description.find("body")-1:]


    return description, input

def ask_gemini(task_description, input):
    prompt = f"""
        You are professional assistant to help crack Advent of Code task. You will be given whole task description and problem input.
        Return FAST python code that will solve the puzzle. Input will be given in file input.txt so please read from that. 
        Only return one answer if there is 2 part please return answer only for that part.
        WRITE ONLY CODE NO EXPLANATION!
        Task description: {task_description}
        Task input: {input}
        Code:
        ```python
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt
    )

    code_by_gemini = response.text.strip('```').replace("python", "")
    return code_by_gemini

def sent_answer(SESSION_KEY, day, answer, star=1):
    url_base = f"https://adventofcode.com/{year}/day/{day}"
    url_answer = url_base + "/answer"
    cookies = {"session": SESSION_KEY}
    data = {"level": star, "answer": answer}

    response_submition = requests.post(url_answer, data=data, cookies=cookies)

    if response_submition.status_code != 200:
        print(f"Error submitting: HTTP {response_submition.status_code}")
        return

    text = response_submition.text

    if "That's the right answer" in text:
        return f"✅ CORRECT! Level of day {day} complete. (star: {star})"
    elif "That's not the right answer" in text:
        return f"❌ WRONG ANSWER"
    elif "You gave an answer too recently" in text:
        return f"Timeout"

    return "WTF man"   

if __name__ == "__main__":
    SESSION_KEY, GEMINI_API_KEY = get_environment()

    client = genai.Client(api_key=GEMINI_API_KEY)

    if len(sys.argv) != 2:
        print("Użycie: python aoc_solver.py <day>")
        raise SystemExit(1)

    try:
        day = int(sys.argv[1])
    except ValueError:
        print("Błąd: Argument <day> musi być liczbą całkowitą.")
        raise SystemExit(1)

    year = 2025

    print("Getting Task description and input...")
    description, input = get_task_description_and_input(SESSION_KEY=SESSION_KEY, year=year, day=day)

    print("Yay we got them!")

    star = 2 if "Part Two" in description else 1 

    print("Saving input for later use...")
    with open("input.txt", "w") as f:
        f.write(input)
    
    print("Asking gemini for help!")
    code = ask_gemini(description, input)

    print("Saving code to a file...")
    with open("solve.py", "w") as f:
        f.write(code)

    print("Running python script")
    answer = subprocess.run(['python', 'solve.py'], capture_output=True, text=True, timeout=15).stdout
    
    print("Sending answer to website")
    done = sent_answer(SESSION_KEY, day, answer, star=star)
    print(f"Result is: {done}")
    with open("result.txt", "w") as f:
        f.write(done)





