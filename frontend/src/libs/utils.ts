export const formatDate = (date: Date): string => {
	const dateFormat: Intl.DateTimeFormatOptions = {
		day: 'numeric',
		month: 'numeric',
		year: 'numeric',
		hour: 'numeric',
		minute: 'numeric',
	};
	return new Date(date).toLocaleDateString('no', dateFormat);
};

export const owners: { [key: string]: string } = {
	'liv.austheim@nte.no': 'Liv Austheim: liv.austheim@nte.no',
	'may-lis.ringseth@nte.no': 'May-Lis: may-lis.ringseth@nte.no',
	'anne.tvestad@nte.no': 'Anne Tvestad: anne.tvestad@nte.no',
	'tonje.ness.meinhardt@nte.no': 'Tonje Ness: tonje.ness.meinhardt@nte.no',
};

export const getOwner = (email: string): string => {
	return owners[email as keyof typeof owners] || 'admin';
};
