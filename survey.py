import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import random
import os
import datetime
import time

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(
    page_title="Восприятие правил посещения футбольных матчей",
    page_icon="⚽",
    layout="centered",
)

# --- ЖЕЛЕЗОБЕТОННЫЙ АВТОСКРОЛЛ ---
def scroll_to_top():
    js_code = """
    <script>
        const elements = window.parent.document.querySelectorAll('.main, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"]');
        elements.forEach(el => el.scrollTo(0, 0));
        window.parent.scrollTo(0, 0);
    </script>
    """
    components.html(js_code, height=0, width=0)

# --- CSS СТИЛИ (Дизайн, равные карточки, шрифты) ---
st.markdown(
    """
    <style>
    .question-text { font-size: 1.06rem; line-height: 1.45; margin: 0 0 6px 0; font-weight: 600; }
    .hint-text { font-size: 0.84rem; line-height: 1.35; color: rgba(120, 120, 120, 0.95); margin: 0 0 10px 0; }
    .section-note { font-size: 0.98rem; line-height: 1.55; margin: 0; }
    
    .vpn-banner {
        background: linear-gradient(135deg, #fff1ee 0%, #ffd8d1 100%);
        border: 1px solid rgba(191, 47, 21, 0.28);
        border-left: 7px solid #bf2f15;
        color: #7e1f10;
        padding: 16px 18px;
        border-radius: 14px;
        margin: 8px 0 20px 0;
        font-size: 1.02rem;
        font-weight: 600;
    }

    .focus-box {
        background: #fbf1ef;
        border: 1px solid rgba(191, 47, 21, 0.20);
        border-left: 6px solid #bf2f15;
        border-radius: 14px;
        padding: 16px 18px;
        margin: 8px 0 18px 0;
    }

    .block-title { font-size: 1.1rem; font-weight: 600; margin: 0 0 12px 0; }
    .question-gap { height: 16px; }

    .thanks-box {
        background: #fff3f0;
        border-left: 7px solid #bf2f15;
        border-radius: 16px;
        padding: 28px 24px;
        margin-top: 20px;
    }
    .thanks-title { font-size: 1.2rem; font-weight: 700; margin-bottom: 10px; color: #1f1f1f; }
    .thanks-text { color: #1f1f1f; }
    
    /* === КАРТОЧКИ ВИНЬЕТОК === */
    .conjoint-wrapper {
        display: flex;
        gap: 20px;
        align-items: stretch; 
        margin-bottom: 20px;
    }
    .conjoint-card {
        flex: 1;
        border: 1px solid rgba(150, 150, 150, 0.3);
        border-radius: 12px;
        padding: 20px;
        background-color: transparent;
    }
    .conjoint-card h3 { margin-top: 0; margin-bottom: 15px; font-size: 1.1rem; font-weight: 600; text-align: center; }
    /* Яркий белый курсив для вступления */
    .conjoint-intro { margin-bottom: 15px; font-size: 0.95rem; font-style: italic; font-weight: bold; color: #ffffff; }
    
    /* Стили для параграфов-атрибутов (без отступов списка) */
    .conjoint-attribute {
        margin-bottom: 12px;
        font-size: 0.95rem;
        line-height: 1.4;
    }
    
    @media (max-width: 768px) {
        .conjoint-wrapper { flex-direction: column; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ВОПРОСОВ ---
def question_gap(): st.markdown("<div class='question-gap'></div>", unsafe_allow_html=True)
def question_text(text: str): st.markdown(f"<div class='question-text'>{text}</div>", unsafe_allow_html=True)
def hint_text(text: str): st.markdown(f"<div class='hint-text'>{text}</div>", unsafe_allow_html=True)

def radio_one(label: str, options, key: str, hint="Выберите один ответ.", horizontal=False):
    question_text(label)
    if hint: hint_text(hint)
    value = st.radio(" ", options, index=None, key=key, label_visibility="collapsed", horizontal=horizontal)
    question_gap()
    return value

def multiselect_one(label: str, options, key: str, hint="Можно выбрать несколько вариантов."):
    question_text(label)
    if hint: hint_text(hint)
    value = st.multiselect(" ", options, key=key, label_visibility="collapsed")
    question_gap()
    return value

def text_input_one(label: str, key: str, hint="Введите ответ."):
    question_text(label)
    if hint: hint_text(hint)
    value = st.text_input(" ", key=key, label_visibility="collapsed")
    question_gap()
    return value

# --- СЛОВАРИ АТРИБУТОВ (С ЭМОДЗИ И БЕЗ БУЛЛИТОВ) ---
ATTRIBUTES = {
    "Зона действия": [
        "📍 Для посещения Вам обязательно понадобится Fan ID, независимо от турнира.",
        "📍 Для посещения Вам понадобится Fan ID, только если матч проводится в рамках Российской Премьер-Лиги.",
        "📍 Вам понадобится Fan ID, только если это матч с принципиальным соперником. Фанаты обоих клубов конкурируют, недолюбливают друг друга."
    ],
    "Механизм бана": [
        "⚖️ Правоохранительные органы могут запретить Вам посещать дальнейшие матчи превентивно, даже без решения суда, просто заподозрив в намерении нарушить порядок.",
        "⚖️ Запретить Вам посещать дальнейшие матчи могут только на основании официально составленного протокола об административном правонарушении на стадионе.",
        "⚖️ Запретить Вам посещать дальнейшие матчи и аннулировать Fan ID могут исключительно по официальному решению суда."
    ],
    "Режим контроля": [
        "👮 ОМОН и полиция дежурят в усиленном режиме как на территории вокруг стадиона, так и внутри — прямо на трибунах и в подтрибунных помещениях.",
        "👮 ОМОН и полиция дежурят только снаружи, вокруг стадиона. Внутри на трибунах правоохранителей нет.",
        "👮 За порядком внутри стадиона следят только стюарды клуба, а сотрудники полиции находятся в резерве далеко за пределами арены."
    ],
    "Цензура": [
        "🚩 Любые баннеры и элементы перформанса Вам необходимо за несколько дней до матча официально согласовывать с органами правопорядка. Пиротехника запрещена",
        "🚩 Предварительно согласовывать баннеры не нужно, но на входе полиция проводит жесткий досмотр и может изъять любые визуальные символы, сочтя их провокационными. Пиротехника запрещена",
        "🚩 Вы можете свободно проносить на трибуну фаеры, баннеры, флаги и символику без предварительного согласования (если они не нарушают законы РФ)."
    ],
    "Позиция актива": [
        "🗣 Активные фанатские группировки призывают к бойкоту: фанатские трибуны пустуют, на стадионе нет привычной атмосферы организованной поддержки.",
        "🗣 Активные фанаты присутствуют на трибунах, но в знак протеста молчат весь матч или демонстративно покидают сектора через 15 минут после начала игры.",
        "🗣 Активные фанаты находятся на трибуне весь матч: они поют, активно используют атрибутику и гонят команду вперед."
    ],
    "Процедура билетов": [
        "🎟 Купить билет себе или другу можно только при условии ввода номера Fan ID и предварительной сдачи биометрии. Спонтанно пойти на матч не получится.",
        "🎟 Вы можете купить билет свободно, однако, чтобы пройти на стадион, Вам все равно придется привязать его к своему номеру Fan ID и предварительно сдать биометрию.",
        "🎟 Вы можете купить и передать билет другу абсолютно свободно, без привязки к Fan ID и обязательной сдачи биометрических данных."
    ]
}

# --- ИНИЦИАЛИЗАЦИЯ ПАМЯТИ ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'responses' not in st.session_state:
    st.session_state.responses = {}
if 'scroll_requested' not in st.session_state:
    st.session_state.scroll_requested = False
if 'conjoint_profiles' not in st.session_state:
    profiles = []
    for _ in range(5):
        prof_a = {attr: random.choice(levels) for attr, levels in ATTRIBUTES.items()}
        prof_b = {attr: random.choice(levels) for attr, levels in ATTRIBUTES.items()}
        while prof_a == prof_b:
            prof_b = {attr: random.choice(levels) for attr, levels in ATTRIBUTES.items()}
        profiles.append({'A': prof_a, 'B': prof_b})
    st.session_state.conjoint_profiles = profiles

# ВЫЗОВ СКРОЛЛА ЕСЛИ БЫЛ ЗАПРОС
if st.session_state.scroll_requested:
    scroll_to_top()
    st.session_state.scroll_requested = False

# --- ФУНКЦИЯ СОХРАНЕНИЯ ---
def save_data():
    data = st.session_state.responses.copy()
    data['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame([data])
    file_name = 'survey_results.csv'
    if not os.path.isfile(file_name): df.to_csv(file_name, index=False, encoding='utf-8-sig')
    else: df.to_csv(file_name, mode='a', header=False, index=False, encoding='utf-8-sig')
    st.session_state.step = 7
    st.session_state.scroll_requested = True

# ==========================================
# ШАГ 1: ПРИВЕТСТВИЕ И ВОПРОСЫ
# ==========================================
if st.session_state.step == 1:
    st.title("Восприятие правил посещения футбольных матчей")
    st.markdown('<div class="vpn-banner">Пожалуйста, выключите VPN перед заполнением анкеты. Это ускорит работу анкеты и снизит вероятность сбоев при отправке ответов.</div>', unsafe_allow_html=True)
    
    st.write("Здравствуйте!\n\nМеня зовут Лев, я студент программы «Политология» НИУ ВШЭ. В рамках написания курсовой работы я провожу академическое исследование о том, как современные болельщики воспринимают правила посещения футбольных матчей в России и реформу FAN ID.\n\nВам предстоит оценить несколько гипотетических сценариев организации матча (с разными правилами доступа, мерами безопасности и т.д.) и отметить, при каких условиях вы бы отправились на стадион, а при каких — предпочли бы остаться дома.\n\nОпрос анонимный и займет около 5–7 минут. В анкете нет правильных или неправильных ответов — важна именно ваша личная точка зрения.\n\nЗаранее большое спасибо за уделенное время и помощь в исследовании!")
    question_gap()
    
    with st.container(border=True):
        st.markdown("<div class='block-title'>Блок 1: О вашем опыте болельщика</div>", unsafe_allow_html=True)
        with st.form("general_questions"):
            q1 = radio_one("Укажите Ваш возраст:", ["Менее 18 лет", "18-24 года", "25-34 года", "35-44 года", "45-54 года", "55 лет и старше"], key="q_age")
            q2 = radio_one("Сколько футбольных матчей примерно Вы посетили за последние 5 лет?", ["Ни одного", "1-4 матча", "5-10 матчей", "11-20 матчей", "Более 20 матчей"], key="q_matches")
            q3_clubs = multiselect_one("За какой российский футбольный клуб Вы болеете?", ["Спартак (Москва)", "ЦСКА (Москва)", "Локомотив (Москва)", "Зенит (Санкт-Петербург)", "Динамо (Москва)", "Нет любимого клуба", "Другой"], key="q_clubs")
            q3_other = text_input_one("Если в предыдущем вопросе Вы выбрали 'Другой', напишите какой именно:", key="q_clubs_other", hint="Если не выбирали, оставьте пустым.")
            q4 = multiselect_one("На какую трибуну (сектор) Вы обычно покупаете/покупали билеты?", ["Фанатская трибуна (сектор за воротами)", "Центральный сектор / Общая трибуна", "Семейный сектор", "Гостевой сектор (на выездных матчах)", "VIP-ложи"], key="q_sector")
            q5 = radio_one("Состоите или состояли ли Вы ранее в организованных фанатских объединениях (фан-клубы, группировки, 'фирмы')?", ["Да, состою в настоящее время", "Да, состоял(а) в прошлом, но сейчас не состою", "Нет, никогда не состоял(а), но поддерживаю / разделяю их взгляды", "Нет, никогда не состоял(а) и отношусь к ним нейтрально/отрицательно"], key="q_firm")
            q6 = radio_one("Оформлен ли у Вас в данный момент 'Паспорт болельщика' (FAN ID)?", ["Да, оформил(а) и продолжаю посещать матчи РПЛ", "Да, оформил(а), но матчи РПЛ принципиально не посещаю", "Нет, принципиально не оформляю (бойкотирую матчи)", "Нет, не оформляю по другим причинам (не связанным с бойкотом)"], key="q_fanid")
            
            q7_income_options = [
                "Я едва свожу концы с концами. Денег не хватает даже на продукты.",
                "На продукты денег хватает, но покупка одежды уже вызывает трудности.",
                "Денег хватает на продукты и одежду, но покупка крупной бытовой техники или мебели уже затруднительна.",
                "Я могу без труда покупать бытовую технику и мебель, но покупка автомобиля уже затруднительна.",
                "Я могу без труда купить автомобиль, но покупка квартиры, дачи или другого дорогого имущества уже затруднительна.",
                "Я могу позволить себе практически все, что считаю нужным."
            ]
            q7 = radio_one("Какое из следующих высказываний точнее всего описывает ваше личное материальное положение?", q7_income_options, key="q_income")
            
            if st.form_submit_button("Перейти к сценариям матча"):
                if not q1 or not q2 or not q4 or not q5 or not q6 or not q7 or (len(q3_clubs) == 0 and not q3_other):
                    st.error("Пожалуйста, ответьте на все обязательные вопросы.")
                # ИСПРАВЛЕННАЯ ЛОГИКА ОТСЕВА (С ИСПОЛЬЗОВАНИЕМ OR)
                elif q1 == "Менее 18 лет" or q2 in ["Ни одного", "1-4 матча"]:
                    st.session_state.step = 8 
                    st.session_state.scroll_requested = True
                    st.rerun()
                else:
                    st.session_state.responses.update({'Возраст': q1, 'Матчей_за_5_лет': q2, 'Клубы': ", ".join(q3_clubs) + (" ("+q3_other+")" if q3_other else ""), 'Сектор': ", ".join(q4), 'Состоит_в_фанатских_объединениях': q5, 'Статус_FanID': q6, 'Доход': q7})
                    st.session_state.step = 2
                    st.session_state.scroll_requested = True
                    st.rerun()

# ==========================================
# ШАГ 2-6: КОНДЖОЙНТ АНАЛИЗ
# ==========================================
elif 2 <= st.session_state.step <= 6:
    pair_index = st.session_state.step - 2
    current_pair = st.session_state.conjoint_profiles[pair_index]
    
    if pair_index == 0:
        st.markdown(
            """
            <div class="focus-box" style="margin-bottom: 25px;">
                <div class="section-note" style="color: #1f1f1f;">
                    Далее Вам будут последовательно представлены 5 пар гипотетических сценариев проведения матча Вашей любимой команды. Пожалуйста, внимательно ознакомьтесь с описанием условий, представленных в карточках.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        st.markdown(f"<div class='block-title'>Сценарий матча {pair_index + 1} из 5</div>", unsafe_allow_html=True)
        
        # Генерация карточек
        def draw_cards(prof_a, prof_b):
            def make_card(p, title):
                html = f"<div class='conjoint-card'><h3>{title}</h3>"
                html += "<div class='conjoint-intro'>Представьте, что Вы собираетесь посетить рядовой матч Вашей любимой команды. Ниже описаны условия проведения данного матча:</div>"
                
                # Выводим атрибуты простыми абзацами
                for key in ["Зона действия", "Механизм бана", "Режим контроля", "Цензура", "Позиция актива", "Процедура билетов"]:
                    html += f"<div class='conjoint-attribute'>{p[key]}</div>"
                html += "</div>"
                return html
                
            return f"<div class='conjoint-wrapper'>{make_card(prof_a, 'Сценарий А')}{make_card(prof_b, 'Сценарий Б')}</div>"

        st.markdown(draw_cards(current_pair['A'], current_pair['B']), unsafe_allow_html=True)
        st.divider()
        
        with st.form(f"conjoint_form_{pair_index}"):
            choice = radio_one("1. На какой матч вы с большей вероятностью пойдете?", ["Сценарий А", "Сценарий Б"], key="c_choice")
            rating_a = radio_one("2. Оцените, с какой вероятностью вы бы пошли на Сценарий А? (Где 1 - точно не пойду, 7 - точно пойду)", [1, 2, 3, 4, 5, 6, 7], key="c_ra", horizontal=True, hint="")
            rating_b = radio_one("3. Оцените, с какой вероятностью вы бы пошли на Сценарий Б? (Где 1 - точно не пойду, 7 - точно пойду)", [1, 2, 3, 4, 5, 6, 7], key="c_rb", horizontal=True, hint="")
            
            if st.form_submit_button("Завершить опрос" if pair_index == 4 else "Следующий сценарий"):
                if not choice or not rating_a or not rating_b:
                    st.error("Ответьте на все 3 вопроса.")
                else:
                    for attr in ATTRIBUTES.keys():
                        st.session_state.responses[f'Pair_{pair_index+1}_Match_A_{attr}'] = current_pair['A'][attr]
                        st.session_state.responses[f'Pair_{pair_index+1}_Match_B_{attr}'] = current_pair['B'][attr]
                    st.session_state.responses.update({f'Pair_{pair_index+1}_Choice': choice, f'Pair_{pair_index+1}_Rating_A': rating_a, f'Pair_{pair_index+1}_Rating_B': rating_b})
                    
                    if pair_index == 4: save_data()
                    else: st.session_state.step += 1
                    
                    st.session_state.scroll_requested = True
                    st.rerun()

# ==========================================
# ШАГ 7 & 8: ЗАВЕРШЕНИЕ
# ==========================================
elif st.session_state.step == 7:
    st.balloons()
    st.markdown('<div class="thanks-box"><div class="thanks-title">Спасибо, ваш ответ успешно записан!</div><div class="thanks-text">Ваши ответы очень помогут в исследовании. Вы можете закрыть вкладку.</div></div>', unsafe_allow_html=True)
elif st.session_state.step == 8:
    st.markdown('<div class="thanks-box"><div class="thanks-title">Опрос завершен.</div><div class="thanks-text">К сожалению, по условиям выборки вы не подходите под критерии. Спасибо за уделенное время!</div></div>', unsafe_allow_html=True)
