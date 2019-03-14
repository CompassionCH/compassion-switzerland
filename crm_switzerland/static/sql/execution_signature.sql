--Define the French signature
SELECT set_signature(
	'Compassion Suisse',
	'Rue Galilée 3',
	'CH-1400 Yverdon-les-Bains',
	'tel: +41 24 434 21 24',
	'fr_CH'
);

--Define the English signature
SELECT set_signature(
	'Compassion Switzerland',
	'Rue Galilée 3',
	'CH-1400 Yverdon-les-Bains',
	'tel: +31 552 21 25',
	'en_US'
);

--Define the German signature
SELECT set_signature(
	'Compassion Schweiz',
	'Effingerstrasse 10',
	'CH-3011 Bern',
	'tel: +41 31 552 21 21',
	'de_DE'
);

--Define the Italian signature
SELECT set_signature(
	'Compassion Svizzera',
	'Effingerstrasse 10',
	'CH-3011 Bern',
	'tel: +41 24 434 21 24',
	'it_IT'
);
