import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--name", required=True)
parser.add_argument("--study", required=True, type=int)
parser.add_argument("--sleep", required=True, type=int)
parser.add_argument("--exercise", required=True)

args = parser.parse_args()

name = args.name
study = args.study
sleep = args.sleep
exercise = args.exercise

score = 0

score = score + study * 10

if sleep >= 7:
    score = score + 20
else:
    score = score + 5

if exercise == "yes":
    score = score + 20

if score >= 80:
    level = "Lv.3"
    title = "오늘 많이 성장한 플레이어"
elif score >= 50:
    level = "Lv.2"
    title = "조금씩 성장하는 플레이어"
else:
    level = "Lv.1"
    title = "이제 시작하는 플레이어"

quests = []

if study < 3:
    quests.append("공부 3시간 이상 하기")

if sleep < 7:
    quests.append("수면 7시간 이상 자기")

if exercise == "no":
    quests.append("10분 산책하기")

print("===== LifeQuest 결과 =====")
print("이름:", name)
print("점수:", score)
print("레벨:", level)
print("칭호:", title)

print()
print("내일의 추천 퀘스트")

for i in range(len(quests)):
    print(str(i + 1) + ".", quests[i])
