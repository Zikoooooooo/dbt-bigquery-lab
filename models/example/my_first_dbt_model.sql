select *
from {{ source('raw_mongo', 'raw_pracownicy') }}