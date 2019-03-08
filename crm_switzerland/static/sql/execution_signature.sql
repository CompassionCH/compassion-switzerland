--Définir la signature Française
SELECT set_signature(
	'Compassion Suisse',
	'Rue Galilée 3',
	'CH-1400 Yverdon-les-Bains',
	'tel: +41 24 434 21 24',
	'fr_CH'
);

--Définir la signature Anglaise
SELECT set_signature(
	'Compassion Switzerland',
	'Rue Galilée 3',
	'CH-1400 Yverdon-les-Bains',
	'tel: +31 552 21 25',
	'en_US'
);

--Définir la signature Allemande
SELECT set_signature(
	'Compassion Schweiz',
	'Rue Galilée 3',
	'CH-3011 Bern',
	'tel: +41 31 552 21 21',
	'de_DE'
);

--Définir la signature Italienne
SELECT set_signature(
	'Compassion Svizzera',
	'Rue Galilée 3',
	'CH-3011 Bern',
	'<span style="color:red;">tel:</<span> +41 24 434 21 24',
	'it_IT'
);

--Définir la signature Espagnole
SELECT set_signature(
	'Compassion Suizo',
	'Rue Galilée 3',
	'CH-1400 Yverdon-les-Bains',
	'tel: +41 24 434 21 24',
	'es_ES'
);