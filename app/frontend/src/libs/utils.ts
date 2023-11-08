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
