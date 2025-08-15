import json, random

brands = ["海信", "小米", "美的", "格力", "飞利浦", "三星", "索尼", "松下", "老板", "九阳", "苏泊尔", "美菱", "TCL", "创维", "海尔", "长虹", "华为", "奥克斯", "西门子", "惠而浦"]
categories = [
    ("电视", "TV"), ("冰箱", "FRIDGE"), ("洗衣机", "WASHER"), ("空调", "AC"), ("按摩椅", "MASSAGE"),
    ("锅具", "COOK"), ("微波炉", "MICROWAVE"), ("电饭煲", "RICECOOKER"), ("挂架", "MOUNT"), ("热水器", "HEATER")
]
addresses = [
    "北京市朝阳区幸福路1号", "上海市浦东新区健康大道88号", "广州市天河区美食街99号", "深圳市南山区科技园路66号",
    "重庆市渝中区解放碑步行街8号", "成都市锦江区春熙路88号", "武汉市武昌区中南路100号", "西安市雁塔区高新路77号",
    "南京市鼓楼区中央路55号", "杭州西湖区文三路99号"
]

users = []
orders = {}
logistics = {}
return_status = {}
refund_status = {}

# 生成100个用户，每人5~10个订单
for uidx in range(100):
    user = {
        "user_id": uidx+1,
        "name": f"用户{uidx+1}",
        "phone": f"138{str(uidx).zfill(8)}",
        "email": f"user{uidx+1}@test.com"
    }
    users.append(user)
    order_count = random.randint(5, 10)
    for oidx in range(order_count):
        brand = random.choice(brands)
        cat_name, cat_code = random.choice(categories)
        order_id = f"{cat_code.lower()}{20250815000+uidx*10+oidx}"
        status = random.choice(["已发货", "已签收", "退货中", "已取消", "待付款", "已完成"])
        amount = round(random.uniform(299, 5999), 2)
        address = random.choice(addresses)
        # 每个订单1~3个商品
        item_count = random.randint(1, 3)
        items = []
        for _ in range(item_count):
            sku = f"{cat_code}-{random.randint(1,99)}"
            items.append({"name": f"{brand}{cat_name}", "sku": sku})
        if random.random() > 0.7:
            items.append({"name": f"{brand}挂架", "sku": f"MOUNT-{random.randint(1,99)}"})
        orders[order_id] = {
            "order_id": order_id,
            "user_id": user["user_id"],
            "status": status,
            "amount": amount,
            "items": items,
            "address": address,
        }
        logistics[order_id] = [
            {"time": "2025-08-15 10:00", "status": "已揽收"},
            {"time": "2025-08-16 09:00", "status": "运输中"},
            {"time": "2025-08-17 15:00", "status": status},
        ]
        for item in items:
            if status in ["退货中", "已完成"]:
                return_status[(order_id, item["sku"])] = random.choice([
                    "退货已收到，正在处理退款", "退货申请已提交，待审核", "退货已完成", "无退换货记录"])
        if status in ["退货中", "已完成"]:
            refund_status[order_id] = random.choice([
                "退款处理中，预计3个工作日到账", "退款已完成", "退款申请已提交，待审核"])

with open("data/users.json", "w", encoding="utf-8") as f:
    json.dump(users, f, ensure_ascii=False, indent=2)
with open("data/orders.json", "w", encoding="utf-8") as f:
    json.dump(orders, f, ensure_ascii=False, indent=2)
with open("data/logistics.json", "w", encoding="utf-8") as f:
    json.dump(logistics, f, ensure_ascii=False, indent=2)
with open("data/return_status.json", "w", encoding="utf-8") as f:
    json.dump({str(k):v for k,v in return_status.items()}, f, ensure_ascii=False, indent=2)
with open("data/refund_status.json", "w", encoding="utf-8") as f:
    json.dump(refund_status, f, ensure_ascii=False, indent=2)
with open("data/brands.json", "w", encoding="utf-8") as f:
    json.dump(brands, f, ensure_ascii=False, indent=2)
with open("data/categories.json", "w", encoding="utf-8") as f:
    json.dump(categories, f, ensure_ascii=False, indent=2)
with open("data/addresses.json", "w", encoding="utf-8") as f:
    json.dump(addresses, f, ensure_ascii=False, indent=2)
