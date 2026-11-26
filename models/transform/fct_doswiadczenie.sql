select
    t.`_id` as pracownik_id,
    d.umiejetnosc,
    d.lata_doswiadczenia
from {{ source('raw_mongo', 'raw_pracownicy') }} as t,
    unnest([
        struct('Java' as umiejetnosc, t.Doswiadczenie.Java as lata_doswiadczenia),
        struct('C++' as umiejetnosc, t.Doswiadczenie.`C++` as lata_doswiadczenia),
        struct('MongoDB' as umiejetnosc, t.Doswiadczenie.MongoDB as lata_doswiadczenia),
        struct('C#' as umiejetnosc, t.Doswiadczenie.`C#` as lata_doswiadczenia),
        struct('Python' as umiejetnosc, t.Doswiadczenie.Python as lata_doswiadczenia),
        struct('Angular' as umiejetnosc, t.Doswiadczenie.Angular as lata_doswiadczenia),
        struct('Elixir' as umiejetnosc, t.Doswiadczenie.Elixir as lata_doswiadczenia),
        struct('Robot' as umiejetnosc, t.Doswiadczenie.Robot as lata_doswiadczenia),
        struct('Selenium' as umiejetnosc, t.Doswiadczenie.Selenium as lata_doswiadczenia),
        struct('SapERP' as umiejetnosc, t.Doswiadczenie.SapERP as lata_doswiadczenia)
    ]) as d
where d.lata_doswiadczenia is not null