CREATE TABLE urls(url VARCHAR(256), short CHAR(7));
CREATE INDEX index_urls_url ON urls (url);
CREATE INDEX index_urls_short ON urls (short);
