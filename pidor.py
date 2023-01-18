import sqlite3
import discord
import random
import datetime

conn = sqlite3.connect("data.db")
with conn:
    conn.execute("""CREATE TABLE IF NOT EXISTS gays (
        user_id int NOT NULL,
        day int NOT NULL,
        month int NOT NULL,
        year int NOT NULL,
        server int NOT NULL
    );""")
    conn.execute("""CREATE TABLE IF NOT EXISTS gay_config (
        server int NOT NULL UNIQUE,
        role int NOT NULL
    );""")

async def select_gay(guild: discord.Guild):
    # feat.:
    # https://github.com/AngryJKirk/familybot
    # @SublimeBot (TG)
    lines = [
        [
            "### Running 'TyPidor.sh'...",
            "Woop-woop! That's the sound of da pidor-police!",
            "Опять в эти ваши игрульки играете? Ну ладно...",
            "Итак... Кто же сегодня пидор дня?",
            "Инициирую поиск пидора дня...",
            "Что тут у нас?",
            "Сейчас поколдуем...",
            "Система взломана. Нанесён урон. Запущено планирование контрмер.",
            "Осторожно! Пидор дня активирован!",
            "Зачем вы меня разбудили...",
            "...",
            "Загоняем всех пидоров в вольер...",
            "Все пидоры в одном помещении.",
            "Вы, не совсем натуралы. Я бы даже сказал совсем НЕ натуралы.",
            "Собрание в церкви святого пидора начинается.",
            "Я собрал всех пидоров вместе.",
            "Петушки собрались в баре \"Голубая устрица\".",
            "Все пидорки увязли в дурно пахнущем болоте...",
            "Голубки, внимание! Ух, как вас много...",
            "Из Техаса к нам присылают только быков и пидорасов. Рогов я у вас не вижу, так что выбор невелик.",
            "ПИДОРЫ, приготовьте свои грязные сральники к разбору полетов!",
            "Объявляю построение пидорской роты!",
            "Загоняємо всіх підорів до вольєру...",
        ],
        [
            "Ведётся поиск в базе данных...",
            "Выезжаю на место...",
            "Интересно...",
            "Сканирую...",
            "КЕК!",
            "Сонно смотрит на бумаги...",
            "\*Ворчит\* А могли бы делом заниматься...",
            "Военный спутник запущен, коды доступа внутри...",
            "Хм...",
            "Шаманим - шаманим...",
            "Машины выехали...",
            "АХТУНГ!",
            "Девочки 🙍‍♀️🙍‍♀️🙍‍♀️записываемся на ноготочки💅💃😻",
            "РААВНЯЯЙСЬ! СМИИРНАА!",
            "Подсудимый, встать!", 
            "Судебное заседание объявляется открытым.",
            "А ну, куда убегаешь!", 
            "Стоять, смирно!"
        ],
        [
            "Не может быть!",
            "Ого-го...",
            "Что с нами стало...",
            "Ох...",
            "Высокий приоритет мобильному юниту!",
            "Я в опасности, системы повреждены!",
            "В этом совершенно нет смысла...",
            "Ведётся захват подозреваемого...",
            "Проверяю данные...",
            "Доступ получен. Аннулирование протокола...",
            "Так-так, что же тут у нас...",
            "Клетка с пидором дня открыта!",
            "Ищем самого возбужденного...",
            "Главный сегодня только один.",
            "Город засыпает, просыпается главный пидор.",
            "Архипидору не скрыться.",
            "У одного задок сегодня послабее...",
            "Ооо, побольше бы таких в нашем клубе!",
            "Сегодня Индиана Джонс в поисках утраченного пидрилы.",
            "Кому-то из вас сегодня ковырнули скорлупку...",
            "У кого-то дымоход почище остальных...",
            "У одного из вас коптильня подогрета...",
            "На грязевые ванные отправляется лишь один...",
            "У когось димохід чистіший, ніж у інших...",
            "Місто засинає, просинається головний підор.",
            "осталось одно место 🙏😍☺️",
            "Кто-то из вас точно не защитник...",
            "Зачитываю приговор...", 
            "Никто из вас не уйдет от настоящего правосудия!",
            "Молодые люди, вам тут расписаться надо.", 
            "Щас документик один подпишем..."
        ],
        [
            "Кажется, пидор дня - ",
            "Что? Где? Когда? А ты пидор дня - ",
            "И прекрасный человек дня сегодня... а, нет, ошибка, всего лишь пидор - ",
            "Стоять! Не двигаться! Вы объявлены пидором дня, ",
            "Ну ты и пидор, ",
            "Пидор дня обыкновенный, 1 шт. - ",
            "Кто бы мог подумать, но пидор дня - ",
            "Ага! Поздравляю! Сегодня ты пидор - ",
            "Анализ завершен. Ты пидор, ",
            """```
.∧＿∧ 
( ･ω･｡)つ━☆・*。 
⊂  ノ    ・゜+. 
しーＪ   °。+ *´¨) 
         .· ´¸.·*´¨) 
          (¸.·´ (¸.·'* ☆
```
ВЖУХ И ТЫ ПИДОР, """,
            "ВЫРВАЛСЯ ВЫРВАЛСЯ ",
            "ХОБАНА! Вижу блеск в глазах ",
            "Воу-воу, полегче... ",
            "Глину месить, это тебе не в тапки ссать, ",
            "ТЫ ЧО ДЫРЯВЫЙ ",
            "Поппенгаген открыт для всех желающих у ",
            "Лупится в туза, но не играет в карты - ",
            "Вонзается плугом в тугой чернозём ",
            "Любитель сделать мясной укол - ",
            "Не лесник, но шебуршит в дупле - ",
            "Кожаная пуля в кожаном стволе у ",
            "Шышл-мышл, пёрнул спермой, вышел, ",
            "Дупа відкрита для всіх охочих у ",
            "Ласує хуями ",
            "Не бачить різниці між вареником у сметані та хуєм у спермі ",
            "ТИ ЩО, ГЕЙ-МОСКАЛЬ? ",
            "Маникюрчик для главной дырки в мясе👸💅👠 ",
            "Не служил - не мужик, ",
            "Бутылка приготовлена для ", 
            "Место у параши уже ждет ",
            "Повестку получает товарищ ", 
            "Сегодняшняя повесточка у "
        ]
    ]
    already = [
        "Нихрена! Пидор - ",
        "Уже выбран. И он - ",
        "Может, лучше спросить ",
        "Ничего нового! Пидор все еще ",
        "Пошел отсюда, еще не время! Пока еще ",
        "По моим данным, это ",
        "Этот чудесный человек - ",
        "Появись, ",
        "Хочешь на место ",
        "Сегодняшний пидор уже обнаружен - ",
        "Сьогоднішній підор вже визначений - ",
        "Сегодняшний задержанный уже осужден - ",
        "Сегодняшняя повестка уже выдана "
    ]
    ranaway = [
        "Я нашла пидора дня, но он сбежал отсюда (Вот пидор!), так что попробуйте еще раз.",
    ]

    date = datetime.date.today()
    members = guild.members
    gay_data = None
    for res in conn.execute("SELECT user_id FROM gays WHERE day=? AND month=? AND year=? AND server=?",(date.day, date.month, date.year, guild.id)):
        gay_data = res
    if gay_data is not None:
        gay = next((gay for gay in members if gay.id == gay_data[0]), None)
        if gay is None:
            return [random.choice(ranaway),]
        return [random.choice(already) + gay.mention,]
    gay = random.choice(members)
    for res in conn.execute("SELECT role FROM gay_config WHERE server=?",(guild.id,)):
        role_id = res[0]
    gay_role = guild.get_role(role_id)
    for member in members:
        if gay_role in member.roles:
            await member.remove_roles(gay_role)
    await gay.add_roles(gay_role)
    res = [random.choice(line) for line in lines]
    res[3] += gay.mention
    with conn:
        conn.execute("INSERT INTO gays VALUES (?,?,?,?,?)",(gay.id, date.day, date.month, date.year, guild.id))
    return res

def gay_stats(guild, period):
    gay_texts = [
        "пробитых жёпок",
        "шебуршаний в дупле",
        "прожаренных сосисок на заднем дворе",
        "разгруженных вагонов с углём",
        "прочищенных дымоходов",
        "волосатых мотороллеров",
        "девственных лесов Камбоджи",
        "шебуртінь у дуплі",
        "засмаленних сосисок на задньому дворі",
        "волохатих мотороллера",
        "дряблых сисек",
        "шершавых вареников",
        "заправленных кроватей",
        "лучших солдатиков",
        "симпатичных сержантиков",
        "посещенных митингов",
        "поднятых плакатов",
        "кинутых стаканчиков",
        "поднятых забрал",
        "экстремистких транспарантов",
        "прибытий в военкомат"
    ]
    date = datetime.date.today()
    match period:
        case "Месяц":
            titles = [
                "Топ пидоров за месяц",
                "Топ підорів за місяц",
                "Топ ефрейторов за месяц",
                "Топ задержанных за месяц",
                "Топ мобилизованных за месяц"
            ]
            gays = []
            for gay in conn.execute("""SELECT user_id, count(user_id) 
                                        FROM gays 
                                        WHERE month=? AND year=? AND server=?
                                        GROUP BY user_id 
                                        ORDER BY count(user_id) DESC""",(date.month, date.year, guild.id)):
                gays.append(gay)
        case "Год":
            titles = [
                "Топ пидоров за год",
                "Топ підорів за рік",
                "Топ ефрейторов за год",
                "Топ задержанных за год",
                "Топ мобилизованных за год"
            ]
            gays = []
            for gay in conn.execute("""SELECT user_id, count(user_id) 
                                        FROM gays 
                                        WHERE year=? AND server=?
                                        GROUP BY user_id 
                                        ORDER BY count(user_id) DESC""",(date.year, guild.id)):
                gays.append(gay)
        case "Все время":
            titles = [
                "Топ пидоров за все время",
                "Топ підорів за весь час",
                "Топ ефрейторов за все время",
                "Топ задержанных за все время",
                "Топ мобилизованных за все время"
            ]
            gays = []
            for gay in conn.execute("""SELECT user_id, count(user_id) 
                                        FROM gays 
                                        WHERE server=?
                                        GROUP BY user_id 
                                        ORDER BY count(user_id) DESC""",(guild.id,)):
                gays.append(gay)
    embeds = []
    embed = discord.Embed()
    embed.title = random.choice(titles)
    if gays == []:
        embed.color = discord.Color.red()
        embed.add_field(name="Ошибка!",value="В списке нет пидоров, пидорасы!")
        return embed
    embed.color = discord.Color.blue()
    gay_list = ""
    count_list = ""
    for gay in gays:
        gay_list += f"<@{gay[0]}>\n"
        count_list += f"{gay[1]} {random.choice(gay_texts)}\n"
        if len(gay_list) > 950 or len(count_list) > 950:
            embed.add_field(name="Пидоры",value=gay_list,inline=True)
            embed.add_field(name="Количество",value=count_list,inline=True)
            embeds.append(embed)
            embed = discord.Embed()
            embed.title = "У-у-у, пидорасы, не влезли"
            embed.color = discord.Color.blue()
            gay_list = ""
            count_list = ""
    embeds.append(embed)
    embed.add_field(name="Пидоры",value=gay_list,inline=True)
    embed.add_field(name="Количество",value=count_list,inline=True)
    return embeds

def set_gay_role(guild, role):
    try:
        with conn:
            conn.execute("INSERT OR IGNORE INTO gay_config VALUES (?,?)",(guild.id, role.id))
            conn.execute("UPDATE gay_config SET role=? WHERE server=?",(role.id, guild.id))
        return True
    except:
        return False