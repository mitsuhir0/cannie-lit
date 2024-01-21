import streamlit as st
from pydantic import BaseModel
from typing import List

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

class Units(BaseModel):
    freshman_seminar: int
    basics: int
    required: int
    elective: int
    course_subjects: int
    other_seminar: int
    other_categories: int
    liberal: int
    language: int
    workshop: int
    all_subjects: int


class Condition(BaseModel):
    name: str
    en: str
    target: int

class Conditions(BaseModel):
    conditions: list[Condition]



freshman = Condition(name="フレッシュマン", en="freshman_seminar", target=4)
basics = Condition(name="基礎科目", en="basics", target=6)
req = Condition(name="必修", en="required", target=2)
elective = Condition(name="選択必修", en="elective", target=26)
course = Condition(name="コース科目", en="course_subjects", target=46)
other = Condition(name="コース外科目", en="other_subjects", target=0)
seminar = Condition(name="演習科目", en="other_seminar", target=12)

conditions = Conditions(
    conditions=[
        freshman,
        basics,
        req,
        elective,
        course,
        other,
        seminar,
    ])

class OtherSubject(BaseModel):
    name: str
    unit: int


class OtherSubjects(BaseModel):
    name: str
    subjects: List[OtherSubject]



model = DataModel.parse_file('./data.json')

l = []
for subject in model.other_categories:
    l.append(OtherSubject(name=subject, unit=0))

other_subjects = OtherSubjects(subjects=l, name="その他")

st.title("Cannie")

course_names = [course.name for course in model.courses]
course_select = st.selectbox(
    "コース",
    course_names
)

tab_list = [condition.name for condition in conditions.conditions]
tab_list.append(other_subjects.name)

tabs = st.tabs(tab_list)

units_dic = {}

course_id = course_names.index(course_select)
course = model.courses[course_id]


with tabs[0]:
    selected = [st.checkbox(label=subject) for subject in model.freshman_seminar]
    units = sum(selected) * 2
    units_dic["freshman_seminar"] = units

with tabs[1]:
    selected = [st.checkbox(label=subject) for subject in model.basics]
    units = sum(selected) * 2
    units_dic["basics"] = units


with tabs[2]:
    selected = [st.checkbox(label=subject) for subject in course.required]
    units = sum(selected) * 2
    units_dic["required"] = units


with tabs[3]:
    selected = [st.checkbox(label=subject) for subject in course.elective]
    units = sum(selected) * 2
    units_dic["elective"] = units


with tabs[4]:
    selected = [st.checkbox(label=subject) for subject in course.course_subjects]
    units = sum(selected) * 2
    units_dic["course_subjects"] = units + units_dic["required"] + units_dic["elective"]
 

with tabs[5]:
    selected = [st.checkbox(label=subject) for subject in course.other_subjects]
    units = sum(selected) * 2
    units_dic["other_subjects"] = units

with tabs[6]:
    selected = [st.checkbox(label=subject) for subject in model.other_seminar]
    units = sum(selected) * 2
    units_dic["other_seminar"] = units

with tabs[7]:
    foreign_language_units = st.checkbox("1外国語で4単位修得している")
    st.write("")
    for subject in other_subjects.subjects:
        unit = st.number_input(subject.name, min_value=0, max_value=100)
        subject.unit = unit

other_total_unit = sum([subject.unit for subject in other_subjects.subjects])
units_dic["other_categories"] = other_total_unit


units_dic['all_subjects'] = (
    units_dic['course_subjects']
    + units_dic['other_subjects']
    + units_dic['other_categories']
)

units_dic["liberal"] = other_subjects.subjects[1].unit
units_dic["language"] = other_subjects.subjects[2].unit
units_dic["workshop"] = other_subjects.subjects[6].unit

units = Units(**units_dic)

if units.freshman_seminar >= freshman.target:
    st.sidebar.write(freshman.name, ' OK')

if units.basics >= basics.target:
    st.sidebar.write(basics.name, ' OK')

if units.basics >= basics.target:
    st.sidebar.write(basics.name, ' OK')

if units.required >= req.target:
    st.sidebar.write(req.name, ' OK')

if units.elective >= elective.target:
    st.sidebar.write(elective.name, ' OK')



def metric(condition: Condition):
    if condition.target > 0:
        label = f"{condition.name}: {condition.target}単位以上"
    else:
        label = f"{condition.name}"
    
    st.sidebar.metric(label=label, value=units_dic[condition.en])

_ = [metric(condition) for condition in conditions.conditions]

st.sidebar.metric(label="教養: 6単位以上", value=units.liberal)
st.sidebar.metric(label="言語: 4単位以上", value=units.language)
st.sidebar.metric(label="関連科目 ワークショップ", value=units.workshop)
st.sidebar.metric(label="修得単位数: 124単位以上", value=units.all_subjects)
