import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Form from 'react-bootstrap/Form';

import AdminLayout from '../../components/Layout/AdminLayout';
import Button from '../../components/Button/Button';

import styles from './CreateSource.module.scss';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheck } from '@fortawesome/pro-regular-svg-icons';
import { faEye, faTrash, faXmark } from '@fortawesome/pro-solid-svg-icons';
import {
	apiFetch,
	ClassificationEnum,
	classificationMap,
	Document,
} from '../../api';
import DocModal from '../../components/Modal/DocModal';
import { formatDate, owners } from '../../libs/utils';
import UrlField from '../../components/UrlField/UrlField';

export function Component(): JSX.Element {
	const [loading, setLoading] = useState<boolean>(true);
	const [viewDocument, setViewDocument] = useState<boolean>(false);
	const [data, setData] = useState<Document>();
	const [isFile, setIsFile] = useState<boolean>(data?.type !== 'web');
	const { id } = useParams();
	const navigate = useNavigate();

	useEffect(() => {
		// fetch data
		getDocument();
	}, []);

	async function getDocument() {
		if (!id) return;

		setLoading(true);

		apiFetch(`/api/documents/${id}`)
			.then(res => res.json())
			.then(res => {
				setData(res);
				setIsFile(res.type !== 'web');
			})
			.catch(err => console.error(err))
			.finally(() => setLoading(false));
	}

	async function updateDocument(e: React.FormEvent<HTMLFormElement>) {
		e.preventDefault();

		if (!id) return;

		setLoading(true);

		// put form values in an object only containing the values that have changed
		const formData = new FormData(e.currentTarget);

		// handle file upload
		const file = formData.get('file') as File;
		if (file && file.name !== data?.file) {
			// send pdf to server
			const fileData = new FormData();
			fileData.append('file', file);

			apiFetch(`/api/documents/${id}/file`, {
				method: 'POST',
				body: fileData,
			}).catch(err => console.error(err));

			formData.delete('file');
		}

		const body: any = { type: isFile ? 'pdf' : 'web' };
		for (const [key, value] of formData.entries()) {
			if (!value || key === 'type') continue;

			if (key === 'urls') {
				const urls = JSON.parse(value as string);

				body.urls = urls.filter((url: string) => url !== '');

				continue;
			}

			if (data && key in data) {
				body[key] = value;
			}
		}

		// if no values have changed, return
		if (Object.keys(body).length === 0) {
			setLoading(false);
			return;
		}

		apiFetch(`/api/documents/${id}`, {
			method: 'PUT',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(body),
		})
			.then(res => res.json())
			.then(res => setData(res))
			.catch(err => console.error(err))
			.finally(() => navigate(-1));
	}

	const handleDeleteItem = () => {
		if (!confirm('Er du sikker på at du vil slette denne kilden?')) return;

		setLoading(true);

		apiFetch(`/api/documents/${id}`, { method: 'DELETE' }).then(() => {
			navigate(-1);
		});
	};

	const getLogLabel = (change?: string) => {
		switch (change) {
			case 'flagged':
				return 'Kilde ble flagget';

			case 'updated':
				return 'Kilde ble oppdatert';

			default:
				return change;
		}
	};

	return (
		<AdminLayout
			className={styles.layout}
			loading={loading}
			breadcrumbs={[
				{
					link: '#',
					text: data?.title,
				},
			]}>
			<h2 className={styles.title}>Endre kilde</h2>

			{!loading && (
				<Form onSubmit={updateDocument}>
					{/* <div className={styles.row}>
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
							/>
						</div>
					</div> */}

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

					{isFile ? (
						<div className={styles.row}>
							<Form.Group>
								<Form.Label>Fil</Form.Label>
								{data?.file ? (
									<div className={styles.fileRow}>
										<span>{data?.file}</span>

										<Button
											type="button"
											variant="danger"
											onClick={() =>
												setData({
													...data,
													file: undefined,
												})
											}
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
								<UrlField
									defaultValue={data?.urls}
									name="urls"
								/>
							</div>

							<div className={styles.row}>
								<Form.Group>
									<Form.Label>
										Oppdateringsfrekvens
									</Form.Label>
									<Form.Select
										aria-label="Velg oppdateringsfrekvens"
										name="frequency"
										defaultValue={data?.frequency}
										required>
										<option>Velg</option>
										<option value="daily">Daglig</option>
										<option value="weekly">Ukentlig</option>
										<option value="monthly">
											Månedtlig
										</option>
									</Form.Select>
								</Form.Group>
							</div>
						</>
					)}

					<div className={styles.row}>
						<Form.Group>
							<Form.Label>Eier</Form.Label>

							<Form.Select
								aria-label="Velg eier"
								name="owner"
								defaultValue={data?.owner}
								required>
								<option>Velg</option>

								<option value="admin">Admin</option>
								{Object.keys(owners).map(key => (
									<option key={key} value={key}>
										{owners[key]}
									</option>
								))}
							</Form.Select>
						</Form.Group>

						<Form.Group>
							<Form.Label>Klassifisering</Form.Label>

							<Form.Select
								aria-label="Velg klassifisering"
								name="classification"
								defaultValue={data?.classification}
								required>
								<option>Velg</option>

								{Object.values(ClassificationEnum).map(
									value => (
										<option key={value} value={value}>
											{classificationMap[value]}
										</option>
									)
								)}
							</Form.Select>
						</Form.Group>
					</div>

					<div className={styles.actions}>
						{isFile && (
							<Button
								variant="outline-primary"
								type="button"
								onClick={() => {
									setViewDocument(true);
									return;
								}}
								icon={<FontAwesomeIcon icon={faEye} />}>
								Se kilde
							</Button>
						)}

						<Button
							variant="outline-danger"
							type="button"
							onClick={() => handleDeleteItem()}
							icon={<FontAwesomeIcon icon={faTrash} />}>
							Slett
						</Button>

						<a href="/admin">Avbryt</a>

						<Button
							type="submit"
							icon={<FontAwesomeIcon icon={faCheck} />}>
							Lagre
						</Button>
					</div>
				</Form>
			)}

			{data?.logs && data?.logs?.length > 0 && (
				<>
					<h2 className={styles.title}>Endringslogg</h2>

					<div className={styles.logList}>
						{data.logs.map((log, i) => (
							<div
								key={log?.id}
								className={`${styles.log} ${
									log.change === 'flagged' &&
									data?.flagged_pages?.length > 0 &&
									i === 0 &&
									styles.flagged
								}`}>
								<div className={styles.logRow}>
									<span className={styles.logTitle}>
										{getLogLabel(log?.change)}
									</span>

									<span className={styles.logTime}>
										{formatDate(log.created_at)}
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

			{data && viewDocument && (
				<DocModal
					onClose={() => setViewDocument(false)}
					document={data}
				/>
			)}
		</AdminLayout>
	);
}

Component.displayName = 'EditSource';
