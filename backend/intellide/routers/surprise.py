import random
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import RedirectResponse, PlainTextResponse

api = APIRouter(prefix="/surprise")


@api.api_route("/echo", response_class=PlainTextResponse)
async def echo(
    request: Request,
):
    body = await request.body()
    if not body:
        return "什么都没有？怎么会这样！"
    return body.decode("utf-8")[::-1]


@api.api_route("/teapot", response_class=PlainTextResponse)
async def teapot():
    raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT, detail="I'm a teapot")


@api.api_route("/ping")
async def ping():
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


@api.api_route("/rickroll")
async def rickroll():
    return RedirectResponse(url="https://www.bilibili.com/video/BV1hq4y1s7VH")


@api.api_route("/time", response_class=PlainTextResponse)
async def time():
    now = datetime.now().strftime("%H:%M")
    if now == "13:14":
        return f"{now}，一个充满故事的时间！"
    return f"当前时间: {now}"


@api.api_route("/status", response_class=PlainTextResponse)
async def status_():
    return "一切运行良好，但开发者今天喝了太多咖啡，所以如果出现问题，可能是代码太快了。"


@api.api_route("/random")
async def random_():
    return 42


@api.api_route("/secret", response_class=PlainTextResponse)
async def secret():
    return random.choice(
        [
            "API 设计的最高境界是让人觉得不需要 API。",
            "服务器 99.99% 的可用性意味着每年仍有 52.56 分钟的宕机时间。",
            "某个 API 维护者已经喝了 3 杯咖啡。",
            "JSON 其实是 JavaScript Object Notation，但 Python 用得比 JavaScript 还多。",
            "程序员的时间计算方式：5 分钟 = 30 分钟，1 小时 = 明天。",
            "API 维护者最怕的三个字：‘能改吗’。",
            "当 API 需要 10 层嵌套 JSON 时，可能你需要重构了。",
            "99% 的 API Bug 都是因为某个地方大小写没对上。",
            "你永远不会相信，HTTP 200 OK 也可能代表错误。",
            "RESTful API 的 REST 不是让你 REST（休息）的意思。",
            "GraphQL 让你少写 API，但让你多写查询。",
            "API 设计的一大原则：不要让调用者崩溃。",
            "如果一个 API 既能返回 200 又能返回 500，那它就是量子态的。",
            "OAuth2.0 的教程能比 JWT 认证的代码还长。",
            "API 里如果需要传 5 个 Token 认证，可能你做错了什么。",
            "永远不要在生产环境里直接返回 Python Traceback。",
            "API 开发最头疼的问题：不同团队对 ‘标准’ 的理解不一样。",
            "API 里的 ‘limit’ 参数设计不合理？小心用户一次请求 1000000 条数据。",
            "最好的 API 是你根本不需要文档就能用的 API。",
            "API 设计原则之一：默认返回 ‘最安全’ 的数据。",
            "如果你需要专门的 API 文档，那说明你没写好 API。",
            "每天早晨，API 维护者的问候语是：‘今天一定不崩溃！’",
            "谁说 API 设计不需要创造力？来一份超复杂的参数嵌套吧！",
            "在使用 API 的过程中，你是否经历过 ‘API 回应：‘我没有问题，问题是你’’ 的时刻？",
            "API 日常：‘你以为我稳定，其实我不稳定’。",
            "API 有时也需要心情调节：如果不高兴，就让你 500 错误。",
            "每个接口都应该有一个 API Token，像一张通行证。",
            "前端：‘为什么每次改个参数都要提交新的 API 请求’？后端：‘这就是 API 的魅力’。",
            "遇到 500 错误时，你不知道发生了什么，但至少你有一些线索。",
            "API 的 Bug 跟你打招呼，‘我今天有点懒，不想工作了’。",
            "在这个世界上，‘控制台’ 就是神的代名词。",
            "你可以对一个 API 做很多优化，但它还是会给你返回一个 500 错误。",
            "每个 API 维护者都有一颗神秘的心脏，时刻准备着处理崩溃。",
            "API 维护者的日常：debug、错误日志、再debug。",
            "API 设计的一个原则：‘越复杂的功能，越应该简化接口’。",
            "没有人能真正理解 API 的设计，除非你亲自做了。",
            "JSON 是 API 的流行语言，但是 CSV 更符合大数据的口味。",
            "API 的逻辑很简单：你的请求，我不处理；我的错误，不能被你处理。",
            "你永远不能满足所有人，特别是在 API 设计时。",
            "API 调用的时候，总觉得‘好像哪里不对’，然后就进了 debug 模式。",
            "你以为你写的 API 很完美，直到有人要求你加一个新功能。",
            "API 中的异常状态码，像时间一样神秘莫测。",
            "设计一个 API 是一种艺术，做文档是哲学。",
            "好的 API 设计是：我给你一份文档，你把它当说明书；坏的 API 设计是：我给你一份说明书，你把它当文档。",
            "重构 API 是对现有系统的慈悲，但也往往让人心情复杂。",
            "API 维护者总是在猜测：是不是服务器宕机了？",
            "API 中的错误代码就像是圣经，解读起来千奇百怪。",
            "每个 API 设计者都需要拥有过目不忘的能力，因为接口太多了。",
            "你写的 API 接口太复杂了，连自己都懒得看。",
            "‘500’ 错误代表着一切都出错了，其他错误你至少能找到一些原因。",
            "API 的异常，通常意味着‘世界末日’。",
            "开发 API 之前，先学会如何给接口设计文档做注释。",
            "API 维护最痛苦的一刻：你写的接口从来没有经过测试。",
            "一个好的 API 设计应该让你感觉它像空气一样自然。",
            "请求参数越多，越容易出错，尤其是列表和字典的嵌套。",
            "API 是一种精神，它告诉你‘不要让用户迷失在参数的海洋里’。",
            "尽量避免在 API 中使用复杂的排序参数，毕竟人类设计不出完美的排序规则。",
            "最好不要为 API 提供 10000 种不同的错误码，除非你是全球最忙的 API 维护者。",
            "最成功的 API 设计是：它看起来简单，实际上背后复杂得可以吓死人。",
            "测试一个 API 接口的第一步：先保证它能调用。",
            "API 里的每一个参数都可能改变一切，尤其是在不经意间。",
            "API 设计其实很像做菜：准备好食材，方法简单却容易失败。",
            "每个 API 的目标都是：让调用者觉得自己用了最简单的方案。",
            "重构 API 代码时，你永远无法预料哪些地方会崩溃。",
            "API 的安全性与稳定性是最难把握的平衡，稍有不慎就会崩溃。",
            "在我们心里，API 返回的状态码就是上天赋予的命运。",
            "错误 403 的神秘力量：你没有权限进入这个数据的世界。",
            "每当 API 返回 200 时，你心里都有一个小小的庆祝仪式。",
            "API 是一种乐趣：它就像是一扇门，背后充满了各种奇妙的可能性。",
            "后端程序员的哲学：‘我没问题，你的问题是你客户端的事’。",
            "API 日常任务：收集错误，修复 bug，再收集错误。",
            "API 接口就像是魔法，调用时它能够让一切变得不同。",
            "API 维护的真理：维护的过程，就是调试与绝望的过程。",
            "API 设计的成功秘诀：满足最常用的需求，忽略那些不常用的需求。",
            "不管你写的 API 多么复杂，总有一个开发者会问：“能不能简单点？”",
            "API 就像魔术师的魔法，往往让你惊讶它的奇妙。",
            "代码总是比文档难写，但好的 API 总能让代码和文档合二为一。",
            "API 文档写得好，代码都不怕错。",
            "最完美的 API 设计是：当你调用时，它就知道你想要什么。",
            "如果 API 能返回 ‘对不起，我理解错了’，那就更完美了。",
            "API 编写的艺术：即使它变得很复杂，也要让用户觉得简单。",
            "API 是最贴心的服务，能做到让你不再感到烦恼。",
            "你写的 API 从不说谎，但总会让你很吃惊。",
            "API 就是神奇的钥匙，打开了各种世界的大门。",
            "API 是魔术师，客户端只是观众。",
            "如果一个 API 设计者很安静，那他一定在想：‘我该怎么解决这个 bug’。",
            "我们希望设计出不会让你迷失在错误中的 API。",
            "API 中的错误往往是谜，等待开发者解开。",
            "每个 API 都有一个密码，找不到就永远打不开。",
            "API 文档：可能是世界上最容易失去耐心的地方。",
            "API 设计，很多时候像是在构建沙盒，谁都不想跳出来。",
            "API 里的每一行代码，都可能改变应用的未来。",
            "API 开发很累，但它也让你更了解‘耐心’。",
        ]
    )


@api.api_route("/devmode")
async def devmode():
    return {
        "status": "ok",
        "message": "Dev Mode: All systems operational.",
        "token": "566h55CG5ZGY5qih5byP77yM5ZCv5Yqo77yB",
    }


@api.api_route("/help", response_class=PlainTextResponse)
async def help_():
    return "您的帮助文档正在赶来的路上，请稍等片刻。"


@api.api_route("/mood", response_class=PlainTextResponse)
async def mood():
    return random.choice(
        [
            "😎 像黄瓜一样冷静",
            "🥺 很累，但还是坚持着",
            "😤 有点沮丧，但还在努力",
            "💀 内心死寂，但还是在写代码",
            "😅 又打错字了…",
            "🤖 我是机器，没人能阻挡我",
            "🤡 今天感觉像个小丑",
            "👻 避开所有任务，但还在这里",
            "💡 灵感四射，准备出发！",
            "🧠 大脑超负荷，但还好",
            "🦄 我是独角兽，别惹我",
            "🤠 今天像个牛仔一样写代码",
            "🎉 跟我的代码一起狂欢",
            "😩 有点不知所措，但我继续前进",
            "🧙‍♂️ 编码巫师，驾驭一切",
            "🥳 准备征服世界（或者至少是代码）",
            "🤯 被自己的牛逼惊呆了",
            "🦾 半人半机器人",
            "🌚 这也太可疑了，这也太奇怪了…",
            "🙃 颠倒的世界，但我搞得定",
            "🥴 勉强坚持着，但还是在动",
            "🕵️‍♂️ 像侦探一样调查Bug",
            "👨‍💻 代码是生命，睡觉是给非开发者的",
            "🌈 在错误的彩虹中编程",
            "💪 比我刚刚修好的Bug还强",
            "🧑‍🚀 执行部署任务的宇航员",
            "⚡ 由咖啡和代码提供动力",
            "💤 睡觉是给非开发者的",
        ]
    )
