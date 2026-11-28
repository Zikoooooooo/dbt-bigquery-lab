{{ config(materialized='table') }}

select
    p.pracownik_id,
    p.imie,
    p.nazwisko,
    round(coalesce(sum(t.godziny), 0)) as suma_godzin
from {{ ref('dim_pracownicy') }} as p
left join {{ ref('trf_transakcje') }} as t
    on p.pracownik_id = t.pracownik_id
group by
    p.pracownik_id, p.imie, p.nazwisko