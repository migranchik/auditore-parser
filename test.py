import asyncio.queues as q
import asyncio

myq = q.Queue(0)


async def worker():
    a = await myq.get()
    print(a)

async def grab():
    while True:
        await myq.put(input())
        print(myq)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker())
    asyncio.run(grab())
