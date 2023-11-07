import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import Form from 'react-bootstrap/Form';

import AdminLayout from '../../components/Layout/AdminLayout';
import Button from '../../components/Button/Button';

import styles from './CreateSource.module.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheck } from '@fortawesome/pro-regular-svg-icons';
import { faEye, faTrash, faXmark } from '@fortawesome/pro-solid-svg-icons';

interface Log {
	user: string;
	change: string;
	id: string;
	message: string;
	created_at: Date;
}

interface Document {
	id: string;
	title: string;
	owner: string;
	classification: string;
	logs: Log[];
	frequency: string;
	flagged: boolean;
	type: string;
	file: string;
	file_pages: string[];
	url: string;
	created_at: Date;
	updated_at: Date;
}

export function Component(): JSX.Element {
	const [data, setData] = useState<Document>();
	const [isFile, setIsFile] = useState<boolean>(data?.type !== 'web');
	const { id } = useParams();

	useEffect(() => {
		if (!id) return;
		// fetch data
		getDocument(id).then(res => setData(res));
	}, []);

	async function getDocument(id: string): Promise<Document> {
		return await fetch(`/api/documents/${id}`).then(res => res.json());
	}

	return (
		<AdminLayout
			className={styles.layout}
			breadcrumbs={[
				{
					link: '#',
					text: data?.title,
				},
			]}>
			<h2 className={styles.title}>Endre kilde</h2>

			<Form>
				<div className={styles.row}>
					<div style={{ display: 'flex', gap: '24px' }}>
						<Form.Check
							type="radio"
							name="type"
							label="Fil"
							checked={isFile}
							onChange={() => setIsFile(true)}
						/>

						<Form.Check
							type="radio"
							name="type"
							label="Nettside"
							checked={!isFile}
							onChange={() => setIsFile(false)}
							disabled
						/>
					</div>
				</div>

				{isFile ? (
					<div className={styles.row}>
						<Form.Group>
							<Form.Label>Fil</Form.Label>
							{data?.file ? (
								<div className={styles.fileRow}>
									<span>{data?.file}</span>
									<Button
										variant="danger"
										icon={
											<FontAwesomeIcon
												icon={faXmark}
												type="button"
											/>
										}>
										Erstatt fil
									</Button>
								</div>
							) : (
								<Form.Control
									name="file"
									type="file"
									required
								/>
							)}
						</Form.Group>
					</div>
				) : (
					<>
						<div className={styles.row}>
							<Form.Group>
								<Form.Label>URL</Form.Label>
								<Form.Control
									name="url"
									defaultValue={data?.url}
									required
								/>
							</Form.Group>
						</div>

						<div className={styles.row}>
							<Form.Group>
								<Form.Label>Oppdateringsfrekvens</Form.Label>
								<Form.Select
									aria-label="Velg oppdateringsfrekvens"
									name="frequency"
									defaultValue={data?.frequency}
									required>
									<option>Velg</option>
									<option value="Daglig">Daglig</option>
									<option value="Ukentlig">Ukentlig</option>
									<option value="Månedtlig">Månedtlig</option>
								</Form.Select>
							</Form.Group>
						</div>
					</>
				)}

				<div className={styles.row}>
					<Form.Group>
						<Form.Label>Tittel</Form.Label>
						<Form.Control
							name="title"
							defaultValue={data?.title}
							required
						/>
					</Form.Group>
				</div>

				<div className={styles.row}>
					<Form.Group>
						<Form.Label>Eier</Form.Label>
						<Form.Select
							aria-label="Velg eier"
							defaultValue={data?.owner}
							required>
							<option>Velg</option>
							<option value="1">One</option>
							<option value="FHI">Erlend Østerås</option>
							<option value="3">Three</option>
						</Form.Select>
					</Form.Group>

					<Form.Group>
						<Form.Label>Klassifisering</Form.Label>
						<Form.Select
							aria-label="Velg klassifisering"
							defaultValue={data?.classification}
							required>
							<option>Velg</option>
							<option value="Offentlig">Offentlig</option>
							<option value="Ekstern">Ekstern</option>
							<option value="3">Three</option>
						</Form.Select>
					</Form.Group>
				</div>

				<div className={styles.actions}>
					<Button
						variant="outline-primary"
						icon={<FontAwesomeIcon icon={faEye} type="button" />}>
						Se kilde
					</Button>

					<Button
						variant="outline-danger"
						icon={<FontAwesomeIcon icon={faTrash} type="button" />}>
						Slett
					</Button>

					<a href="/admin">Avbryt</a>

					<Button
						icon={<FontAwesomeIcon icon={faCheck} type="submit" />}>
						Lagre
					</Button>
				</div>
			</Form>

			{data?.logs && data?.logs?.length > 0 && (
				<>
					<h2 className={styles.title}>Endringslogg</h2>

					<div className={styles.logList}>
						{data.logs.map(log => (
							<div
								key={log?.id}
								className={`${styles.log} ${
									log.change === 'flagged' && styles.flagged
								}`}>
								<div className={styles.logRow}>
									<span className={styles.logTitle}>
										{log.change === 'flagged'
											? 'Kilde ble flagget'
											: log.change}
									</span>

									<span className={styles.logTime}>
										{log?.created_at?.toDateString()}
									</span>
								</div>

								{log.message && (
									<div className={styles.logRow}>
										<span>{log.message}</span>
									</div>
								)}

								<div className={styles.logRow}>
									<span>Av {log.user}</span>
								</div>
							</div>
						))}
					</div>
				</>
			)}
		</AdminLayout>
	);
}

Component.displayName = 'EditSource';
