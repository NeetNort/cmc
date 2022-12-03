""" [NOTE About] '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    [Author] NeetNort
        [Twitter] https://twitter.com/NeetNort
        [Github] https://github.com/NeetNort
    [Date] 12/02/2022
    [Python Version] 3.9.0
    [Description] Helpful utilities for working with CoinMarketCap data
''' /[NOTE About] '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''"""
import sys
from requests import get
from aiohttp import ClientSession
from json import dump
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from datetime import date, timedelta
from typing import Union
from itertools import chain
from asyncio import gather, run, set_event_loop_policy, WindowsSelectorEventLoopPolicy
from TerminalColors import TerminalColors
tc: TerminalColors = TerminalColors()

def generateDateRange(startDate: date, endDate: date) -> list[tuple[str, str]]:
    return [str(startDate + timedelta(days=daysOffset)) for daysOffset in range((endDate - startDate).days + 1)]

async def requestHistoricalDayAsync(convertId: Union[int, str], date: str, limit: Union[int, str], start: Union[int, str], userAgent: str, session: ClientSession) -> list[dict]:
    headers:    dict = {"user-agent": userAgent}
    url: str  = ( 
        f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listings/historical?" +
        f"convertId={convertId}"                                                         + 
        f"&date={date}"                                                                  + 
        f"&limit={limit}"                                                                +
        f"&start={start}"                                                      
    )
    print(f"{tc.cyan}Starting query with url: {url}{tc.end}") # NOTE: Comment this if you don't want output ...
    async with session.get(url, headers=headers) as response:
        responseJson: dict = await response.json()

        if "status" not in responseJson:
            print(f"{tc.red} UNKOWN ERROR! REQUEST STATUS CODE: {response.status_code} | JSON: {responseJson}{tc.end}")
            sys.exit(1)
        error_code:    str  = responseJson["status"]["error_code"]
        error_message: str  = responseJson["status"]["error_message"]
        if error_message != "SUCCESS":
            print(f"{tc.red} ERROR MESSAGE: {error_message} | ERROR CODE: {error_code}")
            sys.exit(1)

        return responseJson["data"]
    
async def getHistoricalDataForDateRangeAsync(
    startDate: date,
    endDate: date,
    convertId: Union[int, str] = 2781,
    startIndex: Union[int, str] = 1,
    limit: Union[int, str] = 200,
    outfilePath: str = "./cmc_data.json"
) -> None:
    userAgentHelper: UserAgent = UserAgent(limit=1000, software_names=[SoftwareName.CHROME.value], operating_systems=[OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value])
    async with ClientSession() as session:
        data: list = list(
            chain.from_iterable(
                await gather(
                    *[
                        requestHistoricalDayAsync(
                            convertId=convertId,
                            date=day,
                            limit=limit,
                            start=startIndex,
                            userAgent=userAgentHelper.get_random_user_agent(),
                            session=session
                        ) for day in generateDateRange(startDate, endDate)
                    ]
                )
            )
        )

        with open(outfilePath, "w", encoding="utf-8") as datafile:
            dump(data, datafile)

if __name__ == "__main__":
    set_event_loop_policy(WindowsSelectorEventLoopPolicy()) # NOTE: Remove if not on windows, unsure how this would be handled on another OS
    run(
        getHistoricalDataForDateRangeAsync(
            startDate=date(2021, 1, 1),                 # NOTE: The first day (inclusive) to query historical data for
            endDate=date(2021, 1, 5),                   # NOTE: The last day (inclusive) to query historical data for
            convertId=2781,                             # NOTE: This should convert the response prices into USD
            startIndex=1,                               # NOTE: The raw coin index in the result set to start from (1 means start with the first coin and return 1 + limit)
            limit=10000,                                # NOTE: The limit of coins to return for each day
            outfilePath="./test.json"                   # NOTE: The outfile directory where the json file will be saved
        )
    )