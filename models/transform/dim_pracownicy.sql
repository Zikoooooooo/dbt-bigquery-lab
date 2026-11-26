select
    `_id` as pracownik_id,
    Imie as imie,
    Nazwisko as nazwisko,
    Staz as staz,
    Miasto as miasto,
    Stanowisko as stanowisko,
    Pensja as pensja
from {{ source('raw_mongo', 'raw_pracownicy') }}