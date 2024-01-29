import { AnalyticsBrowser } from '@segment/analytics-next';

const analytics =
	import.meta.env.MODE === 'development'
		? { track: () => {}, load: () => {} }
		: new AnalyticsBrowser();

analytics.load({
	writeKey: import.meta.env.VITE_SEGMENT_WRITE_KEY,
});

export default analytics;
