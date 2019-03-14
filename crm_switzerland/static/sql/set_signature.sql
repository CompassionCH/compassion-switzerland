DROP FUNCTION set_signature(text,text,text,text,character varying);
CREATE OR REPLACE FUNCTION set_signature(text1 text, text2 text, text3 text, text4 text, wLang varchar)
  RETURNS void AS
$$
DECLARE
	email_banner_url_open   character varying(255);
	email_banner_url   	character varying(255);
BEGIN
	--Deletes translations for the language as a parameter
	DELETE FROM ir_translation
	WHERE name = 'res.users,signature'
		AND lang = wLang
	;
	
	-- Default signature for everyone at the user table is defined in French
	UPDATE res_users users
	SET signature = (SELECT '<span><b>' || p.preferred_name || ' ' || p.lastname || '</b></span><br>' || '<span>Compassion Suisse</span><br>' || '<span>Rue Galilée 3</span><br>' || '<span>CH-1400 Yverdon-les-Bains</span><br>' || '<span>tel: +41 24 434 21 24</span><br>' FROM res_users u INNER JOIN res_partner p ON u.partner_id = p.id where u.id = users.id)
	;

	--Retrieving the parameter for the banner URL
	SELECT value INTO email_banner_url FROM ir_config_parameter
	WHERE key = 'email.banner.url';

	--Retrieving the parameter for the click URL of the banner
	SELECT value INTO email_banner_url_open FROM ir_config_parameter
	WHERE key = 'email.banner.url.open';
	
	--Generate new signatures
	INSERT INTO ir_translation
	SELECT 	nextval('ir_translation_id_seq'::regclass) as id,
		wLang as lang,
		--The SRC signature must match the signature at the table users, otherwise if the user goes in his preferences of the langes of the signature, the system generates new signatures
		(SELECT '<span><b>' || p.preferred_name || ' ' || p.lastname || '</b></span><br>' || '<span>Compassion Suisse</span><br>' || '<span>Rue Galilée 3</span><br>' || '<span>CH-1400 Yverdon-les-Bains</span><br>' || '<span>tel: +41 24 434 21 24</span><br>' FROM res_users u INNER JOIN res_partner p ON u.partner_id = p.id where u.id = users.id) as src,
		'res.users,signature' as name,
		users.id as res_id,
		'base' as module,
		'translated' as slate,
		'<span><b>' || p.preferred_name || ' ' || p.lastname || '</b></span><br>' ||
		'<span>' || text1 || '</span><br>' ||
		'<span>' || text2 || '</span><br>' ||
		'<span>' || text3 || '</span><br>' ||
		'<span>' || text4 || '</span><br>' ||
		'<span><a style="color:#0054a6" href="https://www.compassion.ch/" target="_blank">www.compassion.ch</a></span><br>' ||
		'<span><a href="' || email_banner_url_open || '" target="_blank"><img height="158px" width="640px" src="' || email_banner_url || wLang || '.png"></img></a></span>' as value,
		'model' as model
	FROM res_users users
	INNER JOIN res_partner p
		ON users.partner_id = p.id
	;
END; $$
 
LANGUAGE plpgsql;