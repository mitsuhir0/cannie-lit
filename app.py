"""
「教養」から6単位以上を修得すること。
「言語」から1外国語4単位(必修)以上を修得すること。

基礎科目
6単位修得すること。
規定の単位数を超えて修得した場合は、コース科目の選択必修科目の単位数に充当できる。

コース科目
46単位以上修得すること。
専攻するコース（産業経済コース、公共経済コース、スポーツ経済コース、グローバル・エコノミーコース）の必修科目2単位と選択必修科目26単位を含んで修得すること。

「フレッシュマンゼミナ－ルＡ・Ｂ」・「基礎ゼミナ－ルＡ・Ｂ」・「専門ゼミナールⅠ・Ⅱ・Ⅲ・Ⅳ」は、必ず履修しなければならない。
「フレッシュマンゼミナールＡ」「フレッシュマンゼミナールＢ」の各2単位合計4単位は必修とする。
残り12単位は、基礎科目・コース科目・コース外科目の単位で上限8単位まで、ワークショップの単位で上限8単位までの単位で代替できる。
"""

import streamlit as st
from pydantic import BaseModel
from typing import List
from enum import Enum

def autoselect_basics(A: bool, A2: bool, B:bool, B2:bool):
    # どちらか一方がはじめから条件を満たしているなら他方に基礎ゼミを加算
    if A & (not B):
        return (A, B2)
    elif (not A) & B:
        return (A2, B)
        
    # 加算前にはいずれも条件を満たしておらず、
    elif (not A) & (not B):
        # 基礎ゼミの加算によっていずれも条件を満たすなら
        # どちらの条件を満たしたいかユーザーに選ばせる
        if A2 & B2: 
            selected_elective = "**選択必修科目に加算する**"
            selected_semi = "**演習科目に加算する**"
            choice = st.sidebar.radio("❓ **基礎科目を…**",
                          [
                              selected_elective,
                              selected_semi
                              ])
            if choice is selected_elective:
                return (A2, B)
            elif choice is selected_semi:
                return (A, B2)
            else: 
                return (A2, B)
        # 加算によってどちらか一方のみが条件を満たすなら、
        # 自動的にそれを選ぶ
        elif (not A) & B2:
            return (A, B2)
        elif A2 & (not B):
            return (A2, B)
        
        # 基礎ゼミを加算しても、いずれも条件を満たさないときな、
        # 便宜的にAに加算する
        elif (not A2) & (not B2):
            return (A2, B)
        else:
            KeyError


class Course(BaseModel):
    id: int
    name: str
    required: List[str]
    elective: List[str]
    course_subjects: List[str]
    other_subjects: List[str]


class DataModel(BaseModel):
    courses: List[Course]
    basics: List[str]
    freshman_seminar: List[str]
    other_seminar: List[str]
    other_categories: List[str]


class Unit(BaseModel):
    name: str
    unit: int = 0
    criteria: int | None = None
    is_okay: bool | None = None


class Units(BaseModel):
    freshman_seminar: Unit
    basics: Unit 
    required: Unit 
    elective: Unit
    course_subjects: Unit
    other_subjects: Unit
    other_seminar: Unit
    other_categories: Unit
    liberal: Unit
    language: Unit
    workshop: Unit
    all_subjects: Unit


units = Units(
    freshman_seminar = Unit(name="フレッシュマン", criteria=4)
    , basics = Unit(name="基礎科目", criteria=6)
    , required = Unit(name="必修", criteria=2)
    , elective = Unit(name="選択必修", criteria=26)
    , course_subjects = Unit(name="コース科目", criteria=46)
    , other_subjects = Unit(name="コース外科目")
    , other_seminar = Unit(name="演習科目", criteria=12)
    , other_categories = Unit(name="その他")
    , liberal = Unit(name="教養科目", criteria=6)
    , language = Unit(name="言語", criteria=4)
    , workshop = Unit(name="ワークショップ")
    , all_subjects = Unit(name="計", criteria=124)
)


class OtherSubject(BaseModel):
    name: str
    unit: int = 0


class OtherSubjects(BaseModel):
    name: str
    subjects: List[OtherSubject]

model = DataModel.parse_file('./data.json')

l = []
for subject in model.other_categories:
    l.append(OtherSubject(name=subject, unit=0))

other_subjects = OtherSubjects(subjects=l, name="その他")

st.title("Cannie")
st.text("ご利用は自己責任で")

course_names = [course.name for course in model.courses]
course_select = st.selectbox(
    "コース",
    course_names
)


tabs = st.tabs(
    [
        units.freshman_seminar.name
        , units.basics.name
        , units.required.name
        , units.elective.name
        , units.course_subjects.name
        , units.other_subjects.name
        , units.other_seminar.name
        , units.other_categories.name
    ])

units_dic = {}

course_id = course_names.index(course_select)
course = model.courses[course_id]


with tabs[0]:
    selected = [st.checkbox(label=subject) for subject in model.freshman_seminar]
    units.freshman_seminar.unit = sum(selected) * 2

with tabs[1]:
    selected = [st.checkbox(label=subject) for subject in model.basics]
    units.basics.unit = sum(selected) * 2

with tabs[2]:
    selected = [st.checkbox(label=subject) for subject in course.required]
    units.required.unit = sum(selected) * 2

with tabs[3]:
    selected = [st.checkbox(label=subject) for subject in course.elective]
    units.elective.unit = sum(selected) * 2

with tabs[4]:
    selected = [st.checkbox(label=subject) for subject in course.course_subjects]
    units.course_subjects.unit = sum(selected)*2 + units.required.unit + units.elective.unit

with tabs[5]:
    selected = [st.checkbox(label=subject) for subject in course.other_subjects]
    units.other_subjects.unit = sum(selected) * 2

with tabs[6]:
    selected = [st.checkbox(label=subject) for subject in model.other_seminar]
    units.other_seminar.unit = sum(selected) * 2

with tabs[7]:
    language_is_okay = st.checkbox("1外国語で4単位修得している")
    st.write("")
    for subject in other_subjects.subjects:
        unit = st.number_input(subject.name, min_value=0, max_value=100)
        subject.unit = unit


other_total_unit = sum([subject.unit for subject in other_subjects.subjects])
units.other_categories.unit = other_total_unit

units.liberal.unit = other_subjects.subjects[1].unit
units.language.unit = other_subjects.subjects[2].unit
units.workshop.unit = other_subjects.subjects[6].unit

units.all_subjects.unit = (
    units.freshman_seminar.unit
    + units.basics.unit
    + units.course_subjects.unit
    + units.other_subjects.unit
    + units.other_categories.unit
    ) 

def judge(category: Unit):
    if category.unit >= category.criteria:
        category.is_okay = True
    else:
        category.is_okay = False


judge(units.freshman_seminar)
judge(units.basics)
judge(units.required)
judge(units.elective)
judge(units.course_subjects)
judge(units.other_seminar)
judge(units.liberal)
judge(units.language)
judge(units.all_subjects)


# 不足単位計算
class Shortage(BaseModel):
    name: str
    unit: int

class Surplus(BaseModel):
    name: str
    unit: int

def gen_shortage(unit: Unit) -> dict:
    return {
        "name": unit.name,
        "unit": unit.unit - unit.criteria
    }

def gen_surplus(unit: Unit) -> dict:
    return {
        "name": unit.name,
        "unit": max(unit.unit - unit.criteria, 0)
    }

ele = Shortage(**gen_shortage(units.elective))
cou_shortage = Shortage(**gen_shortage(units.course_subjects))
semi = Shortage(**gen_shortage(units.other_seminar))
cou_surplus = Surplus(**gen_surplus(units.course_subjects))
other = Surplus(
    name=units.other_subjects.name,
    unit=units.other_subjects.unit
    )
workshop = Surplus(
    name=units.workshop.name,
    unit=units.workshop.unit
    )


class Choise(str, Enum):
    course = "course"
    seminar = "seminar"
    not_selected = "not_selected"

class Basics(BaseModel):
    name: str = "基礎ゼミナール"
    unit: int
    choice: Choise = "not_selected"

basics = Basics(
    name=units.basics.name,
    unit=max(units.basics.unit-units.basics.criteria, 0),
    choice="not_selected"
    )


def add_semi(semi: Shortage, other: Surplus, course: Surplus, workshop: Surplus, basics: Basics) -> int:
    if basics.choice == ("not_selected" or "course"):
        add_basics = 0
    elif basics.choice == "seminar":
        add_basics = basics.unit
    else:
        KeyError
    result = (
        semi.unit
        + min(add_basics + course.unit + other.unit, 8) # 上限8単位
        + min(workshop.unit, 8) # 上限8単位
    )
    return result

def add_course(elective: Shortage, course: Shortage, basics: Basics) -> (int, int):
    if basics.choice == ("not_selected" or "seminar"):
        add_basics = 0
    elif basics.choice == ("course"):
        add_basics = basics.unit
    else:
        KeyError
    ele = elective.unit + add_basics
    cou = course.unit + add_basics
    return (ele, cou)


# まずはworkshop, コース科目、コース外科目を加算 (基礎科目は加算しない)
result = add_semi(semi=semi, other=other, course=cou_surplus, workshop=workshop, basics=basics)
cond_semi = result >= 0
cond_ele = ele.unit >= 0
cond_course = cou_shortage.unit >=0

A = cond_ele & cond_course
B = cond_semi

# 条件を満たしているなら基礎ゼミは加算しない
if A & B:
    pass 

# 条件を満たしていなくても、基礎ゼミに余剰がなければ考慮しない
elif basics.unit == 0:
    pass

# そうでなければ、ゼミと選択必修のそれぞれに基礎ゼミを加算してみて、
# どちらの状況で得をするかシミュレーションする
else:
    # ゼミの方を加算
    basics.choice = "seminar"
    result2 = add_semi(semi=semi, other=other, course=cou_surplus, workshop=workshop, basics=basics)
    B2 = result2 >= 0

    # 選択必修の方を加算
    basics.choice = "course"
    (ele2, course2) = add_course(elective=ele, course=cou_shortage, basics=basics)
    cond_ele2 = ele2 >= 0
    cond_course2 = course2 >= 0
    A2 = cond_ele2 & cond_course2

    (newA, newB) = autoselect_basics(A, A2, B, B2)
    # newAがfalseのときは元のままでOK
    if newA:
        A = newA
    B = newB

units.elective.is_okay = A
units.course_subjects.is_okay = A
units.other_seminar.is_okay = B

achievements = (
    units.freshman_seminar.is_okay
    + units.basics.is_okay
    + units.required.is_okay
    + units.elective.is_okay
    + units.course_subjects.is_okay
    + units.other_seminar.is_okay
    + units.liberal.is_okay
    + units.language.is_okay
    + units.all_subjects.is_okay
)

total_achievements = achievements + language_is_okay


label = f"条件達成 {total_achievements}/10"
if total_achievements == 10:
    st.sidebar.markdown("## " + label +  " 🎉🎉🎉")
else:
    st.sidebar.markdown(label)


def metric(category: Unit):
    if category.criteria is not None:
        if category.is_okay:
            checkmark = "✅"
        else:
            checkmark = "☐"
        label = checkmark + f" {category.name}: {category.criteria}単位以上"
    else:
        label = f"{category.name}"
    st.sidebar.metric(label=label, value=category.unit)

def metric_language(cond):
    if cond:
        checkmark = "✅"
    else:
        checkmark = "☐"
    st.sidebar.text(f"{checkmark} 1外国語で4単位以上")

metric(units.all_subjects)
metric(units.liberal)
metric(units.language)
metric_language(language_is_okay)
metric(units.freshman_seminar)
metric(units.basics)
metric(units.required)
metric(units.elective)
metric(units.course_subjects)
metric(units.other_seminar)
metric(units.other_subjects)
metric(units.workshop)
