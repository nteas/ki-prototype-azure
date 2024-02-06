import { useMemo, useState } from 'react';
import Layout from '../../components/Layout/Layout';
import styles from './Logs.module.scss';
import { getChatLogs } from '../../api';

export interface Log {
	uuid: string;
	feedback: string;
	comment: string;
	thought_process: string;
	timestamp: number;
}

export function Component(): JSX.Element {
	const [logs, setLogs] = useState<Log[]>([]);
	const [log, setLog] = useState<Log | null>();

	useMemo(() => {
		getChatLogs().then(logs => setLogs(logs));
	}, []);

	return (
		<Layout>
			<h1>Logs</h1>

			<div className={styles.logs}>
				{logs?.map((log, i) => (
					<div
						key={i}
						className={styles.log}
						onClick={() => setLog(log)}>
						<span>{log.feedback}</span>
						<span>{log.uuid}</span>
						<span>{log.comment}</span>
						<span>{new Date(log.timestamp).toLocaleString()}</span>
					</div>
				))}
			</div>

			{log && (
				<div className={styles.modalWrapper}>
					<div
						className={styles.overlay}
						onClick={() => setLog(null)}
					/>

					<div className={styles.modal}>
						<div
							dangerouslySetInnerHTML={{
								__html: log.thought_process,
							}}
						/>
					</div>
				</div>
			)}
		</Layout>
	);
}