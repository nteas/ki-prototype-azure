import { useNavigate } from 'react-router-dom';
import { faCheck } from '@fortawesome/pro-regular-svg-icons';
import { useState } from 'react';
import Form from 'react-bootstrap/Form';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

import AdminLayout from '../../components/Layout/AdminLayout';
import Button from '../../components/Button/Button';

import styles from './CreateSource.module.css';
import { ClassificationEnum, classificationMap } from '../../api/models';
import { apiFetch } from '../../api';

export function Component(): JSX.Element {
	const [loading, setLoading] = useState<boolean>(false);
	const [isFile, setIsFile] = useState<boolean>(true);
	const [fileName, setFileName] = useState<string>('');
	const navigate = useNavigate();

	async function createDocument(e: React.FormEvent<HTMLFormElement>) {
		e.preventDefault();

		setLoading(true);

		// put form values in an object only containing the values that have changed
		const formData = new FormData(e.currentTarget);

		const body: any = { type: isFile ? 'pdf' : 'web' };
		for (const [key, value] of formData.entries()) {
			console.log(key, value);

			if (key === 'type' || !value) continue;

			if (key === 'file' && value instanceof File) {
				body['file'] = value.name;
				continue;
			}

			body[key] = value;
		}

		console.log(body);

		// if no values have changed, return
		if (Object.keys(body).length === 0) {
			setLoading(false);
			return;
		}

		const newDoc = await apiFetch(`/api/documents/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(body),
		})
			.then(res => res.json())
			.catch(err => console.error(err));

		// handle file upload
		const file = formData.get('file') as File;
		if (file) {
			// send pdf to server
			const fileData = new FormData();
			fileData.append('file', file);

			await apiFetch(`/api/documents/${newDoc.id}/file`, {
				method: 'POST',
				body: fileData,
			}).catch(err => console.error(err));
		}

		navigate(-1);
	}

	return (
		<AdminLayout
			className={styles.layout}
			loading={loading}
			breadcrumbs={[
				{
					link: '#',
					text: 'Legg til kilde',
				},
			]}>
			<h2 className={styles.title}>Legg til kilde</h2>

			<Form onSubmit={createDocument}>
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
							<Form.Control
								name="file"
								type="file"
								required
								onChange={(
									e: React.ChangeEvent<HTMLInputElement>
								) =>
									setFileName(
										e?.target?.files?.length
											? e?.target?.files[0]?.name
											: ''
									)
								}
							/>
						</Form.Group>
					</div>
				) : (
					<>
						<div className={styles.row}>
							<Form.Group>
								<Form.Label>URL</Form.Label>
								<Form.Control name="url" required />
							</Form.Group>
						</div>

						<div className={styles.row}>
							<Form.Group>
								<Form.Label>Oppdateringsfrekvens</Form.Label>
								<Form.Select
									aria-label="Velg oppdateringsfrekvens"
									name="frequency"
									required>
									<option>Velg</option>
									<option value="1">Daglig</option>
									<option value="2">Ukentlig</option>
									<option value="3">Månedtlig</option>
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
							defaultValue={fileName}
							required
						/>
					</Form.Group>
				</div>

				<div className={styles.row}>
					<Form.Group>
						<Form.Label>Eier</Form.Label>
						<Form.Select
							aria-label="Velg eier"
							name="owner"
							required>
							<option>Velg</option>
							<option value="admin">Admin</option>
							<option value="Telekom">Telekom</option>
							<option value="Kundeservice">Kundeservice</option>
						</Form.Select>
					</Form.Group>

					<Form.Group>
						<Form.Label>Klassifisering</Form.Label>
						<Form.Select
							aria-label="Velg klassifisering"
							name="classification"
							required>
							<option>Velg</option>

							{Object.values(ClassificationEnum).map(value => (
								<option key={value} value={value}>
									{classificationMap[value]}
								</option>
							))}
						</Form.Select>
					</Form.Group>
				</div>

				<div className={styles.actions}>
					<a href="/admin">Avbryt</a>

					<Button
						icon={<FontAwesomeIcon icon={faCheck} type="submit" />}>
						Lagre
					</Button>
				</div>
			</Form>
		</AdminLayout>
	);
}

Component.displayName = 'CreateSource';
