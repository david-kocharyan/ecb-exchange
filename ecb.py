import datetime
import os
import requests
from xml.etree import ElementTree as ET
import pandas as pd

FROM_CURRENCIES = ["EUR", "USD", "JPY", "BGN", "CZK", "DKK", "GBP", "HUF", "PLN", "RON", "SEK", "CHF", "ISK", "NOK",
                   "HRK", "RUB", "TRY", "AUD", "BRL", "CAD", "CNY", "HKD", "IDR", "ILS", "INR", "KRW", "MXN", "MYR",
                   "NZD", "PHP", "SGD", "THB", "ZAR"]
TO_CURRENCIES = ["EUR", "USD", "JPY", "BGN", "CZK", "DKK", "GBP", "HUF", "PLN", "RON", "SEK", "CHF", "ISK", "NOK",
                 "HRK", "RUB", "TRY", "AUD", "BRL", "CAD", "CNY", "HKD", "IDR", "ILS", "INR", "KRW", "MXN", "MYR",
                 "NZD", "PHP", "SGD", "THB", "ZAR"]

FROM_DATE = '2022-04-07'
TO_DATE = '2022-04-09'


def get_ecb_data(from_date, to_date, key):
    # The web service entry point is available at the following location:
    wsEntryPoint = 'https://sdw-wsrest.ecb.europa.eu/service'

    # The resource for data queries is data
    resource = 'data'

    # A reference to the dataflow describing the data that needs to be returned.
    flowRef = 'EXR'

    # Base url
    request_url = f"{wsEntryPoint}/{resource}/{flowRef}/{key}"

    result = ''
    while not result:
        response = requests.get(request_url,
                                params={'detail': 'dataonly', 'startPeriod': from_date, 'endPeriod': to_date})

        if not response.ok:
            raise Exception("The currency rate could not be fetched because the response was incorrect.")

        if not response.text:
            from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
            to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d')
            new_from_date = (from_date - datetime.timedelta(days=1)).date()
            new_to_date = (to_date - datetime.timedelta(days=1)).date()
            from_date = new_from_date.strftime("%Y-%m-%d")
            to_date = new_to_date.strftime("%Y-%m-%d")

        result = response.text
    return result


def get_ecb_rates_with_dates(text):
    currencies = []
    dates = set()

    root = ET.fromstring(text)
    ns = {'generic': "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic",
          'message': "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"}

    series = root.findall('./message:DataSet/generic:Series', ns)

    for index, data in enumerate(series):
        currency_type = data.find('./generic:SeriesKey/generic:Value[@id="CURRENCY"]', ns)
        from_currency = "EUR"
        to_currency = currency_type.get('value')
        pair = f"{from_currency}-{to_currency}"

        obs_value = data.findall('./generic:Obs/generic:ObsValue', ns)
        obs_dimension = data.findall('./generic:Obs/generic:ObsDimension', ns)
        for i, dimension in enumerate(obs_dimension):
            rate = obs_value[i].get('value')
            date = obs_dimension[i].get('value')
            dates.add(date)
            currencies.append({
                "pair": pair,
                "from": from_currency,
                "to": to_currency,
                "rate": rate,
                "date": date,
            })

    return currencies, dates


def calculate_other_currencies(from_currencies, to_currencies, currencies, dates):
    new_currencies = []
    for from_currency in from_currencies:
        for to_currency in to_currencies:
            # Exclude EUR cause we are already have it
            if from_currency == "EUR" or to_currency == "EUR":
                continue

            # Exclude same currencies and calculate others
            if from_currency != to_currency:
                from_rate, to_rate = 0, 0
                for date in dates:
                    for currency in currencies:
                        if currency.get('to') == from_currency and currency.get('date') == date:
                            from_rate = float(currency.get('rate'))
                        if currency.get('to') == to_currency and currency.get('date') == date:
                            to_rate = float(currency.get('rate'))
                    if from_rate == 0 or to_rate == 0:
                        new_currencies.append(
                            {
                                "pair": f"{from_currency}-{to_currency}",
                                "from": from_currency,
                                "to": to_currency,
                                "rate": "There is no data for this pair",
                                "date": date,
                            }
                        )
                    else:
                        new_currencies.append(
                            {
                                "pair": f"{from_currency}-{to_currency}",
                                "from": from_currency,
                                "to": to_currency,
                                "rate": str(round(to_rate / from_rate, 4)),
                                "date": date,
                            }
                        )

    return new_currencies


def exchange(from_currencies, to_currencies, from_date, to_date, with_euro=True, format='csv'):
    # Separate unique fot this 2 lists` from_currencies and to_currencies and join with + for ECB API
    all_unique_currency = set(from_currencies + to_currencies)
    all_unique_currency.discard('EUR')
    key_component = "+".join(all_unique_currency)

    key = 'D.{}.EUR.SP00.A'.format(key_component)

    # ECB API responce
    response = get_ecb_data(from_date, to_date, key)

    # Get dates and currencies against the EUR
    currencies, dates = get_ecb_rates_with_dates(response)

    # Calculate other currencies pairs
    other_currencies = calculate_other_currencies(from_currencies, to_currencies, currencies, dates)

    # Collect all data
    all_data = currencies + other_currencies if with_euro else other_currencies

    # Create a pandas Dataframe with columns
    df = pd.DataFrame(all_data, columns=["pair", "from", "to", "rate", "date"])

    # Check direction
    output_dir = './output'
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    if format == 'csv':
        fullname = os.path.join(output_dir, f"ecb_{from_date}-{to_date}.csv")
        df.to_csv(fullname)
    elif format == 'json':
        fullname = os.path.join(output_dir, f"ecb_{from_date}-{to_date}.json")
        df.to_json(fullname, orient='records')
    else:
        raise Exception("Incorrect format.")


if __name__ == "__main__":
    print("Start")
    start = datetime.datetime.now()

    exchange(FROM_CURRENCIES, TO_CURRENCIES, FROM_DATE, TO_DATE, with_euro=True, format='csv')

    stop = datetime.datetime.now() - start
    print('Time: ', stop)
    print("END")
