import pytest

from importers.comdirect import ComdirectImporter, NoNewBalanceException
from textwrap import dedent
from datetime import datetime

IBAN = 'DE99 1234 1234 1234 1234 99'

@pytest.fixture
def tmp_file(tmp_path):
    file_path = tmp_path / 'umseatze_5873596814_20240522-1438.csv'
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
    

def test_new_balance_absent(tmp_file):
    importer = ComdirectImporter('Assets:MyBank:Checking', IBAN)
    tmp_file.write_text(
        dedent(
            """
            ;
            "Umsätze Girokonto";"Zeitraum: 30 Tage";
            "Buchungstag";......
            """
        ).strip(), encoding="iso-8859-1"
    )
    with tmp_file.open(encoding="ISO-8859-1") as fd:
        try:
            result = importer.extract(fd)
        except NoNewBalanceException:
            assert False
        else:
            assert True
        
        
        
def test_extract_end_date(tmp_file):
    importer = ComdirectImporter('Assets:MyBank:Checking', IBAN)
    date_end = importer.extract_end_date(str('"Umsätze Girokonto";"Zeitraum: 30 Tage";'), tmp_file.name)
    date = datetime(2024, 5, 22, 14, 38)
    assert date_end == date




