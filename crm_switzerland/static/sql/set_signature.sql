DROP FUNCTION set_signature(text,text,text,text,character varying);
CREATE OR REPLACE FUNCTION set_signature(text1 text, text2 text, text3 text, text4 text, wLang varchar)
  RETURNS void AS
$$
DECLARE
	email_banner_url_open   character varying(255);
	email_banner_url   	character varying(255);
BEGIN
	--Supprime les traductions pour la langue en paramètre
	DELETE FROM ir_translation
	WHERE name = 'res.users,signature'
		AND lang = wLang
		--AND res_id = 1
	;
	
	-- Signature par défaut chez tout le monde au niveau de la table user est défini en français	
	UPDATE res_users users
	SET signature = (SELECT '<span><b>' || p.firstname || ' ' || p.lastname || '</b></span><br>' || '<span>Compassion Suisse</span><br>' || '<span>Rue Galilée 3</span><br>' || '<span>CH-1400 Yverdon-les-Bains</span><br>' || '<span>tel: +41 24 434 21 24</span><br>' FROM res_users u INNER JOIN res_partner p ON u.partner_id = p.id where u.id = users.id)
	--WHERE users.id = 1
	;

	--Récupération du paramètre pour l'URL de la bannière
	SELECT value INTO email_banner_url FROM ir_config_parameter
	WHERE key = 'email.banner.url';

	--Récupération du paramètre pour l'URL sur click de la bannière
	SELECT value INTO email_banner_url_open FROM ir_config_parameter
	WHERE key = 'email.banner.url.open';
	
	--Génère les nouvelles signatures
	INSERT INTO ir_translation
	SELECT 	nextval('ir_translation_id_seq'::regclass) as id,
		wLang as lang,
		--La signature SRC doit correspondre à la signature au niveau de la table users, sinon si l'utilisateur va dans ses préférences des langes de la signature, le système génère des nouvelles signatures
		(SELECT '<span><b>' || p.firstname || ' ' || p.lastname || '</b></span><br>' || '<span>Compassion Suisse</span><br>' || '<span>Rue Galilée 3</span><br>' || '<span>CH-1400 Yverdon-les-Bains</span><br>' || '<span>tel: +41 24 434 21 24</span><br>' FROM res_users u INNER JOIN res_partner p ON u.partner_id = p.id where u.id = users.id) as src,
		'res.users,signature' as name,
		users.id as res_id,
		'base' as module,
		'translated' as slate,
		'<span><b>' || p.firstname || ' ' || p.lastname || '</b></span><br>' ||
		'<span>' || text1 || '</span><br>' ||
		'<span>' || text2 || '</span><br>' ||
		'<span>' || text3 || '</span><br>' ||
		'<span>' || text4 || '</span><br>' ||
		'<span><a style="color:rgb(149,79,114)" href="http://www.compassion.ch/" target="_blank">www.compassion.ch</a></span><br>' ||
		'<span><a href="' || email_banner_url_open || '" target="_blank"><img height="158px" width="640px" src="' || email_banner_url || wLang || '.png"></img></a></span>' as value,
		'model' as model
	FROM res_users users
	INNER JOIN res_partner p
		ON users.partner_id = p.id
	--where users.id = 1
	;
END; $$
 
LANGUAGE plpgsql;