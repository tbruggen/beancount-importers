import pytest

from importers.comdirect import ComdirectImporter, NoNewBalanceException
from textwrap import dedent
from datetime import datetime, timedelta
from beancount.ingest import regression


IBAN = 'DE99 1234 1234 1234 1234 99'

@pytest.fixture
def tmp_file(tmp_path):
    file_path = tmp_path / 'umsaetze_1188536237_20240901-1606.csv'
    with open(file_path, 'w', encoding='iso-8859-1') as f:
        pass  # Create an empty file or write initial content if needed
    return file_path

def test_identify_not_correct(tmp_file):
    importer = ComdirectImporter('Assets:MyBank:Checking', IBAN)
    tmp_file.write_text("Hello, World!")   
    with tmp_file.open() as fd:        
        assert not importer.identify(fd)

def test_identify_correct(tmp_file):
    importer = ComdirectImporter('Assets:MyBank:Checking', IBAN)
    tmp_file.write_text(
        dedent(
            """
            ;
            "Umsätze Girokonto";"Zeitraum: 30 Tage";
            "Neuer Kontostand";"7.511,15 EUR";

            
            "Alter Kontostand";"5.994,00 EUR";
            """
        ).strip(), encoding="iso-8859-1"
    )
    with tmp_file.open(encoding="ISO-8859-1") as fd:       
        assert importer.identify(fd)
    

# def test_new_balance_absent(tmp_file):
#     importer = ComdirectImporter('Assets:MyBank:Checking', IBAN)
#     tmp_file.write_text(
#         dedent(
#             """
#             ;
#             "Umsätze Girokonto";"Zeitraum: 30 Tage";
#             "Buchungstag";......
#             """
#         ).strip(), encoding="iso-8859-1"
#     )
#     with tmp_file.open(encoding="ISO-8859-1") as fd:
#         try:
#             result = importer.extract(fd)
#         except NoNewBalanceException:
#             assert False
#         else:
#             assert True
        
        
        
def test_extract_dates(tmp_file):
    importer = ComdirectImporter('Assets:MyBank:Checking', IBAN)
    [start, end] = importer.extract_dates(str('"Umsätze Girokonto";"Zeitraum: 30 Tage";'), tmp_file.name)
    end_date = datetime(2024, 9, 1)
    d = timedelta(days = 30)
    start_date = end_date - d
    assert start_date == start
    assert end_date == end




def test_extract_dates_from_content(tmp_file):
    importer = ComdirectImporter('Assets:MyBank:Checking', IBAN)
    [start, end] = importer.extract_dates(str('"Umsätze Girokonto";"Zeitraum: 01.06.2024 - 09.06.2024";'), tmp_file.name)
    end_date = datetime(2024, 6, 9).date()
    assert end == end_date
    start_date = datetime(2024, 6, 1).date()


def test_extract_balance():
    importer = ComdirectImporter('Assets:MyBank:Checking', IBAN)
    balance, currency = importer.extract_balance('"Neuer Kontostand";"4.588,30 EUR";')
    assert currency == 'EUR'
    assert balance == 4588.30



def test_extract_transactions(tmp_file):
    importer = ComdirectImporter('Assets:MyBank:Checking', IBAN)
    transactions = importer.extract(tmp_file)
    
