CREATE TABLE programs (
   id integer,
   category varchar(500),
   description varchar(500000),
   country varchar(60),
   city varchar(100),
   max_age integer,
   min_age integer,
   cost integer,
   title varchar(500),
   website varchar(5000)
);

.separator ','
.import data.csv programs
