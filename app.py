"""
Cannie

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
import json
import streamlit as st
from pydantic import BaseModel
from typing import List
from enum import Enum


class Course(BaseModel):
    """コース選択によって科目群が変わる"""
    id: int
    name: str
    required: List[str]
    elective: List[str]
    course_subjects: List[str]
    other_subjects: List[str]


class DataModel(BaseModel):
    """json読み込み用データ
    コース選択によって変わるものとコース共通のもの
    """
    courses: List[Course]
    basics: List[str]
    freshman_seminar: List[str]
    other_seminar: List[str]
    other_categories: List[str]


class Unit(BaseModel):
    """
    卒業のために name 科目 をcriteria 単位以上の修得が必要
    """
    name: str
    unit: int = 0
    criteria: int | None = None
    is_okay: bool | None = None


class Units(BaseModel):
    """
    - フレッシュマンゼミナール
    - 基礎ゼミナール
    - 必修科目
    - 選択必修科目
    - コース科目
    - コース外科目
    - 演習科目(基礎ゼミ、専門ゼミ)
    - 教養
    - 言語
    - ワークショップ
    - 全ての科目
    """
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


class OtherSubject(BaseModel):
    """
    その他の科目
    この項目は他と違い、科目の一覧があるのではなく、
    修得した単位数を入力するので、別のデータモデルが必要
    """
    name: str
    unit: int = 0


class OtherSubjects(BaseModel):
    """
    その他の科目のリスト
    units.other_categories と対応
    """
    name: str
    subjects: List[OtherSubject]


class Choice(str, Enum):
    """
    > 基礎科目
    > 規定の単位数を超えて修得した場合は、コース科目の選択必修科目の単位数に充当できる。
    > (演習科目)
    > 残り12単位は、**基礎科目**・コース科目・コース外科目の単位で上限8単位まで、ワークショップの単位で上限8単位までの単位で代替できる。
    このことから、基礎科目を選択必修か演習科目のどちらに充当(代替)するかを選ぶ局面が生じる。
    """
    course = "course"
    seminar = "seminar"
    not_selected = "not_selected"


class Basics(BaseModel):
    """
    基礎科目専用モデル
    ここでの unit は修得単位数でなく 超過分 (>= 0) である
    """
    name: str = "基礎科目"
    unit: int
    choice: Choice = "not_selected"


class Shortage(BaseModel):
    """
    不足単位数の計算に用いるデータ型
    unit は不足単位数
    充当(代替)の可能性がある 選択必修科目、コース科目、演習科目が相当
    """
    name: str
    unit: int


class Surplus(BaseModel):
    """
    不足単位数の計算に用いるデータ型
    unit は 充当(代替)可能な単位数
    基礎科目は専用型を持つ。ここではワークショップ、コース科目、コース外科目が相当
    ※ コース科目は不足・超過両方の可能性がある
    """
    name: str
    unit: int


def gen_shortage(unit: Unit) -> dict:
    """
    Shortageクラスをつくるための辞書を作るヘルパー関数
    """
    return {
        "name": unit.name,
        "unit": unit.unit - unit.criteria
    }


def gen_surplus(unit: Unit) -> dict:
    """
    Surplusクラスをつくるための辞書を作るヘルパー関数
    """
    return {
        "name": unit.name,
        "unit": max(unit.unit - unit.criteria, 0)
    }


def update_ACB(A: bool, C: bool, B: bool, A2: bool, C2: bool, B2: bool) -> Choice:
    """
    C, Bを先に比較して後からA, Cを比較する
    ロジックはC, BもA, B も同じ
    """
    if A is True:                               # 選択必修は足りているけどコース科目が足りていないケース
        match (C, B, C2, B2):
            case (True, True, _, _):            # 元から満たしているなら
                return Choice("not_selected")   # アップデートしない
            case (True, False, _, _):           # どちらかが満たしていないなら
                return Choice("seminar")        # 満たしていない方をアップデート
            case (False, True, _, _):
                return Choice("course")
            case (False, False, True, False):   # どちらも満たしてなくて、アップデートによりどちらかが満たすなら
                return Choice("course")         # そちらをアップデート
            case (False, False, False, True):
                return Choice("seminar")
            case (False, False, False, False):  # どちらも満たしていなくて、アップデートによっても満たさないなら
                return Choice("not_selected")            
            case (False, False, True, True):    # どちらも満たしていなくて、アップデートによりいずれも満たすなら
                return select_basics()

            
    conditions = (A, B, A2, B2)
    match conditions:                   
        case (True, True, _, _):            # 元から満たしているなら
            return Choice("not_selected")   # アップデートしない
        case (True, False, _, _):           # どちらかが満たしていないなら
            return Choice("seminar")        # 満たしていない方をアップデート
        case (False, True, _, _):
            return Choice("course")
        case (False, False, True, False):   # どちらも満たしてなくて、アップデートによりどちらかが満たすなら
            return Choice("course")         # そちらをアップデート
        case (False, False, False, True):
            return Choice("seminar")
        case (False, False, False, False):  # どちらも満たしていなくて、アップデートによっても満たさないなら
            return Choice("not_selected")            
        case (False, False, True, True):    # どちらも満たしていなくて、アップデートによりいずれも満たすなら
            return select_basics()


def select_basics() -> Choice:
    selected_elective = "**選択必修科目に加算する**"
    selected_semi = "**演習科目に加算する**"
    choice = st.sidebar.radio("❓ **基礎科目を…**",
                  [
                      selected_elective,
                      selected_semi
                      ])
    if choice is selected_elective:
        return Choice("course")
    elif choice is selected_semi:
        return Choice("seminar")
    else: 
        return Choice("not_selected")


def judge(category: Unit):
    """
    Unitをとり、条件を満たすかどうかを(1次)判定する関数
    category.is_okay は後に充当(代替)によって変化しうる
    ※判定が変わっても修得単位数は変化させない
    """
    if category.unit >= category.criteria:
        category.is_okay = True
    else:
        category.is_okay = False


def add_semi(seminar: Shortage, other: Surplus, course: Surplus, workshop: Surplus, basics: Basics) -> int:
    """
    > 演習科目
    > 残り12単位は、基礎科目・コース科目・コース外科目の単位で上限8単位まで、
    > ワークショップの単位で上限8単位までの単位で代替できる。

    これをやるための関数。
    ただし基礎科目はコース科目・選択必修科目に充当している場合、二重に充当できないので注意する
    basics.choice の状態で分岐する
    """
    if basics.choice == ("not_selected" or "course"):
        add_basics = 0
    elif basics.choice == "seminar":
        add_basics = basics.unit
    else:
        KeyError

    result = (
        seminar.unit
        + min(add_basics + course.unit + other.unit, 8) # 上限8単位
        + min(workshop.unit, 8) # 上限8単位
    )
    return result


def add_course(elective: Shortage, course: Shortage, basics: Basics) -> (int, int):
    """
    > 基礎科目
    > 6単位修得すること。
    > 規定の単位数を超えて修得した場合は、コース科目の選択必修科目の単位数に充当できる。

    これをやる関数。ただし基礎科目を演習科目で代替していた場合には充当できない
    """
    if basics.choice == ("not_selected" or "seminar"):
        add_basics = 0
    elif basics.choice == ("course"):
        add_basics = basics.unit
    else:
        KeyError

    unit_elective = elective.unit + add_basics
    unit_course = course.unit + add_basics
    return (unit_elective, unit_course)


def update_judge(units: Units, A: bool, C: bool, B: bool):
    """"
    A, C, B に基づいて条件判定を更新する
    A: 選択必修科目の新しい条件
    C: コース科目の新しい条件
    B: 演習科目の新しい条件
    """
    units.elective.is_okay = A
    units.course_subjects.is_okay = C
    units.other_seminar.is_okay = B


def metric(category: Unit):
    """
    個別条件を表示させるヘルパー関数
    """
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
    """
    外国後条件を表示させるだけの関数
    """
    if cond:
        checkmark = "✅"
    else:
        checkmark = "☐"
    st.sidebar.text(f"{checkmark} 1外国語で4単位以上")


# 卒業判定に必要な科目群
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

# コース別科目一覧を読み込み
with open('./data.json', 'r') as f:
    json_data = json.load(f)

model = DataModel.model_validate(json_data)

# その他の科目用データの作成
l = []
for subject in model.other_categories:
    l.append(OtherSubject(name=subject, unit=0))
other_subjects = OtherSubjects(subjects=l, name="その他")


# タイトル
st.title("Cannie")
st.text("ご利用は自己責任で")

# コース選択
course_names = [course.name for course in model.courses]
course_select = st.selectbox(
    "コース",
    course_names
)

# タブの作成
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


# タブの選択結果に対応するタブを表示
# 各タブにはチェックボックスまたは 値のinput
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


# その他の科目で入力された数の集計
other_total_unit = sum([subject.unit for subject in other_subjects.subjects])
units.other_categories.unit = other_total_unit

# 教養・言語・ワークショップに抽出(1, 2, 6 は手作業)
units.liberal.unit = other_subjects.subjects[1].unit
units.language.unit = other_subjects.subjects[2].unit
units.workshop.unit = other_subjects.subjects[6].unit

# 合計修得単位数の計算
units.all_subjects.unit = (
    units.freshman_seminar.unit
    + units.basics.unit
    + units.course_subjects.unit
    + units.other_subjects.unit
    + units.other_categories.unit
    ) 


# 条件の1次判定
judge(units.freshman_seminar)
judge(units.basics)
judge(units.required)
judge(units.elective)
judge(units.course_subjects)
judge(units.other_seminar)
judge(units.liberal)
judge(units.language)
judge(units.all_subjects)


# 不足単位の充当または代替の計算
################################

# 不足している可能性がある科目
shortage_elective = Shortage.model_validate(gen_shortage(units.elective))
shortage_course = Shortage(**gen_shortage(units.course_subjects))
shortage_seminar = Shortage(**gen_shortage(units.other_seminar))

# 充当・代替に用いる科目
surplus_course = Surplus(**gen_surplus(units.course_subjects))
surplus_other = Surplus(
    name=units.other_subjects.name,
    unit=units.other_subjects.unit
    )
surplus_workshop = Surplus(
    name=units.workshop.name,
    unit=units.workshop.unit
    )
surplus_basics = Basics(
    name=units.basics.name
    , unit=max(units.basics.unit-units.basics.criteria, 0)
    , choice="not_selected"
    )

# A: 選択必修科目で不足が生じているかどうか
# 過不足を調整した結果、条件を満たせば非負になる
A = shortage_elective.unit >= 0 

# C: コース科目で不足が生じているか
C = shortage_course.unit >= 0

# B: workshop, コース科目、コース外科目を演習科目に加算したのち、不足があるか否か
# (この段階では基礎科目は加算しない, basics.choice is not selected)
result = add_semi(
    seminar=shortage_seminar
    , other=surplus_other
    , course=surplus_course 
    , workshop=surplus_workshop 
    , basics=surplus_basics
    )
B = result >= 0

# A2: 基礎科目を選択必修の方に加算した場合
surplus_basics.choice = "course"
(val1, val2) = add_course(
    elective=shortage_elective
    , course=shortage_course
    , basics=surplus_basics
    )
A2 = (val1 >= 0)
C2 = (val2 >= 0)

# 基礎科目を演習科目に加算した場合
surplus_basics.choice = "seminar"
val = add_semi(
    seminar=shortage_seminar
    , other=surplus_other
    , course=surplus_course
    , workshop=surplus_workshop
    , basics=surplus_basics
    )
B2 = (val >= 0)

choice: Choice = update_ACB(A, C, B, A2, C2, B2) 
match choice:
    case "not_selected":
        newA = A
        newC = C
        newB = B
    case "seminar":
        newA = A
        newC = C
        newB = B2
    case "course":
        newA = A2
        newC = C2
        newB = B


# 条件判定の更新
update_judge(units, newA, newC, newB)


# 条件を満たした数を集計
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
    + language_is_okay  # 1科目のみで4単位 
)


# 条件達成状況の表示
label = f"条件達成 {achievements}/10"
if achievements == 10:
    st.sidebar.markdown("## " + label +  " 🎉🎉🎉")
else:
    st.sidebar.markdown(label)

# サイドバーに条件達成状況を表示
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