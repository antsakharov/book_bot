import asyncio
async def msg_delete(msg, delay):
    await asyncio.sleep(delay)
    await msg.delete()