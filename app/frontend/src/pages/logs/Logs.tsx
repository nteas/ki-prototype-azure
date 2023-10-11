import { useMemo, useState } from 'react';
import Layout from '../../components/Layout/Layout';
import styles from './Logs.module.css';

interface Log {
	uuid: string;
	feedback: string;
	thought_process: string;
	timestamp: number;
}

export function Component(): JSX.Element {
	const [logs, setLogs] = useState<Log[]>([]);
	const [log, setLog] = useState<Log>();

	useMemo(() => {
		fetch('/logs')
			.then(res => res.json())
			.then(data => setLogs(data));
	}, []);

	return (
		<Layout>
			<div className={styles.wrapper}>
				<h1>Logs</h1>

				<div className={styles.logs}>
					{logs.map((log, i) => (
						<div
							key={i}
							className={styles.log}
							onClick={() => setLog(log)}>
							<span>{log.uuid}</span>
							<span>{log.feedback}</span>
							<span>{log.timestamp}</span>
						</div>
					))}
				</div>

				{log && (
					<div className={styles.logModal}>
						<div>{log.thought_process}</div>
					</div>
				)}
			</div>
		</Layout>
	);
}

Component.displayName = 'OneShot';
