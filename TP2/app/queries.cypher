// schema.cypher

CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (cat:Category) REQUIRE cat.id IS UNIQUE;
CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT order_id_unique IF NOT EXISTS FOR (o:Order) REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;

CREATE INDEX customer_join_date_index IF NOT EXISTS FOR (c:Customer) ON (c.joinDate);
CREATE INDEX product_price_index IF NOT EXISTS FOR (p:Product) ON (p.price);
CREATE INDEX event_timestamp_index IF NOT EXISTS FOR (e:Event) ON (e.timestamp);