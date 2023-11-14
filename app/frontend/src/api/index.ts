export * from './api';
export * from './models';

export async function apiFetch(
	url: string,
	options: RequestInit = {}
): Promise<Response> {
	options.headers = {
		...options.headers,
		userId: localStorage.getItem('ajs_user_id') || '',
	};

	return await fetch(url, options);
}
