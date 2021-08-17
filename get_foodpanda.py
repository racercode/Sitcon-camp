import json
import os
from dislash import SelectMenu, SelectOption, InteractionClient
import discord as dc
import asyncio
import googlemaps
from discord.ext import commands
from dotenv import load_dotenv
import requests as rq

bot = commands.Bot(command_prefix='##')
slash = InteractionClient(bot)

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

payload = {"q":"starbucks","location":{"point":{"latitude":22.6394924,"longitude":120.302583}},"config":"Variant21","customer_id  ":"","vertical_types":["restaurants"],"include_component_types":["vendors"],"include_fields":["feed"],"language_id":"6","opening    _type":"delivery","platform":"web","session_id":"","language_code":"zh","customer_type":"regular","limit":10,"offset":0,"dps_se  ssion_id":"eyJzZXNzaW9uX2lkIjoiMzhhOGUwZTBmYTllZmNlMGIzZTM4ZjNkZDFiMzE4ZjkiLCJwZXJzZXVzX2lkIjoiMTYyODg0ODk0NC42NTQzNzg4MjU2LjQxe    E05NHIxSDgiLCJ0aW1lc3RhbXAiOjE2Mjg5NDYwMDV9","dynamic_pricing":0,"brand":"foodpanda","country_code":"tw","use_free_delivery_la  bel":False}

headers = {
        'content-type': "application/json",
    }

ahead = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.73'
}

@bot.event
async def on_ready():
    channel = bot.get_channel(871443543732912163)
    await channel.send('點餐機器人啟動')

tot = 0 # 餐點數(不用理他)
user_tot = 0 # 總人數(不用理他)
user_num = {} # dictionary, 代表每個人的編號, 用法：user_num[message.author] -> 代碼
user_bought = [] # 二維陣列，每個人買了什麼東西，用法：user_bought[user_num[message.author]] -> 這是一個單維陣列，元素皆為tuple(餐點代碼,註解)
user_cost = [] # 一維陣列，每個人總共花的錢，用法：user_cost[user_num[message.author]] -> 錢錢
dish = [] # 一維陣列，利用餐點代碼存取，裡面的元素都是tuple(價格,名稱)



used = False
entered = False
keyword = ''
user = ''
@bot.event
async def on_message(message):
    global used, entered, keyword, tot, user_tot, user_num, user_bought, user_cost, dish
    string = message.content
    if string.startswith('##init') :
        string,a = string.split(' ')
        
        address = a
        geocode_result = gmaps.geocode(address)
        a = geocode_result[0]["geometry"]["location"]["lat"]
        b = geocode_result[0]["geometry"]["location"]["lng"]
        payload['location']['point']['latitude'] = float(a)
        payload['location']['point']['longitude'] = float(b)
        entered = True
        await message.channel.send('定位成功 !')
    elif string.startswith('##clear') :
        used = False
        keyword = ''
        tot = user_tot = all_sost = user_cost = 0
        user_num = {}
        user_bought = all_dished = dish = []
        await message.channel.send('查詢資料清除成功')
    elif string.startswith('##search') :
        
        if entered == False :
            await message.channel.send('請先輸入你家地址...嘿嘿')
        elif used == True :
            await message.channel.send('都不看訊息的對不對')
        else :
            used = True
            user = message.author
            string,keyword = string.split(' ')

            now_payload = payload
            now_payload['q'] = keyword
            r = rq.post('https://disco.deliveryhero.io/search/api/v1/feed', data = json.dumps(now_payload), headers = headers)
            
            rt_list = json.loads(r.text)
            if len(rt_list['feed']['items']) == 0 :
                await message.channel.send('你家太鄉下囉')
                return
            r_list = rt_list['feed']['items'][0]['items']
        
            embed = dc.Embed(
                title = '請選擇所要的餐廳'
            )
            for i in range(1,6) :
                embed.add_field(name=f'{i}. {r_list[i-1]["name"]}',value=f'評價 {r_list[i-1]["rating"]} 顆星, 外送{r_list[i-1]["minimum_delivery_fee"]} 元以上, {r_list[i-1]["minimum_delivery_time"]} 分鐘送達',inline=False)
            
            await message.channel.send(embed=embed)

            reply=await message.channel.send("請選擇",components=[
                SelectMenu(
                    placeholder="請選所想要的餐廳",
                    max_values=1,
                    options=[
                        SelectOption(f'{1}. {r_list[0]["name"]}','1'),
                        SelectOption(f'{2}. {r_list[1]["name"]}','2'),
                        SelectOption(f'{3}. {r_list[2]["name"]}','3'),
                        SelectOption(f'{4}. {r_list[3]["name"]}','4'),
                        SelectOption(f'{5}. {r_list[4]["name"]}','5')
                    ]
                )
            ]
            )

            inter = await reply.wait_for_dropdown()
            labels = [option.label for option in inter.select_menu.selected_options]
    
            await inter.reply(f"已選擇選項: {', '.join(labels)}")

            option = int(labels[0][0])-1
            code = r_list[option]['code']
            url = 'https://tw.fd-api.com/api/v5/vendors/' + code + '?include=menus&language_id=6&dynamic_pricing=0&opening_type=delivery&basket_currency=TWD&latitude='+str(payload['location']['point']['latitude']) + '&longitude=' + str(payload['location']['point']['longitude'])
            nr = rq.get(url=url,headers=ahead)
            dic = json.loads(nr.text)
            
            for j in dic['data']['menus'][0]['menu_categories'] :
                em = dc.Embed(
                    title = j['name']
                )
                for i in j['products'] :
                    flag = False
                    if i['product_variations'][0]['price']==0 :
                        flag=True
                        break
                    ret = '價格：' + str(i['product_variations'][0]['price']) + '\n' + i['description'] + '\n'
                    em.add_field(name=f'{tot+1}. {i["name"]}', value=ret, inline=False)
                    tup = (int(i['product_variations'][0]['price']), i['name'])
                    dish.append(tup)
                    tot += 1

                if flag == False :
                    await message.channel.send(embed=em)
        
    elif string.startswith('##buy') :
        string, a, b = string.split(' ')
        if int(a)-1>=tot or int(a)<=0:
            await message.channel.send('有事嗎')
            return 
        tup = (int(a)-1,b)
        user = message.author
        if user in user_num :
            user_cost[user_num[user]] += dish[int(a)-1][0]
            user_bought[user_num[user]].append(tup)
        else :
            user_num[user] = user_tot
            user_tot += 1
            user_cost.append(dish[int(a)-1][0])
            user_bought.append([tup])
        await message.channel.send(f'成功購買 !')
        if user_bought[user_num[user]]%3==0 :
            await message.channel.send('讓我想想...你應該是肥宅...')
        all_cost += dish[int(a)-1][0]

    elif string.startswith('##check') :
        user = message.author
        if user not in user_num or len(user_bought[user_num[user]])==0 :
            await message.channel.send('您尚未購買任何餐點 🍱')
            return 
        user = message.author
        embed = dc.Embed(
            title = f'{user} 累計{user_cost[user_num[user]]}元，已購買：'
            )
        total = 1
        for i in user_bought[user_num[user]] :
            embed.add_field(name=f'{total}：{dish[i[0]][1]}, 價格：{dish[i[0]][0]}', value=i[1], inline=False)
            total += 1
        await message.channel.send(embed=embed)
    
    elif string.startswith('##erase'):
        user = message.author
        string,a = string.split(' ')
        a = int(a)
        if a>len([user_bought[user_num[user]]]) or a<=0 :
            await message.channel.send('這選項...你是要我怎樣 🤬 🤬 🤬 🤬 🤬 🤬')
            return 
        user_cost[user_num[user]] -= dish[user_bought[user_num[user]][a-1][0]][0]
        all_cost -= dish[user_bought[user_num[user]][a-1][0]][0]
        del user_bought[user_num[user]][a-1]

        await message.channel.send('移除品項 & 瘦身成功')
    elif string.startswith('##end') :
        for i in user_num :
            for j in user_bought[user_num[i]]:
                all_dished.append(j)
        all_dished.sort()
        embed=dc.Embed(
            title=f'總價格：{all_cost}元'
        )
        for i in range(0,len(all_dished)) :
            embed.add_field(name=dish[all_dished[i][0]][1],value=all_dished[i][1],inline=False)
        await message.channel.send(embed=embed)
        await message.channel.send('##clear') 

bot.run(os.getenv('TOKEN'))
