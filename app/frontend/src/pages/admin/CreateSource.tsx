import Form from 'react-bootstrap/Form';

import AdminLayout from '../../components/Layout/AdminLayout';
import Button from '../../components/Button/Button';

import styles from './CreateSource.module.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheck } from '@fortawesome/pro-regular-svg-icons';

export function Component(): JSX.Element {
	return (
		<AdminLayout
			className={styles.layout}
			breadcrumbs={[
				{
					link: '#',
					text: 'Legg til kilde',
				},
			]}>
			<h2 className={styles.title}>Legg til kilde</h2>

			<Form>
				<div className={styles.row}>
					<div style={{ display: 'flex', gap: '24px' }}>
						<Form.Check
							type="radio"
							name="type"
							label="Fil"
							defaultChecked={true}
						/>

						<Form.Check type="radio" name="type" label="Nettside" />
					</div>
				</div>

				<div className={styles.row}>
					<Form.Group>
						<Form.Label>Fil</Form.Label>
						<Form.Control name="file" type="file" required />
					</Form.Group>
				</div>

				<div className={styles.row}>
					<Form.Group>
						<Form.Label>Tittel</Form.Label>
						<Form.Control name="title" required />
					</Form.Group>
				</div>

				<div className={styles.row}>
					<Form.Group>
						<Form.Label>Eier</Form.Label>
						<Form.Select aria-label="Velg eier" required>
							<option>Velg</option>
							<option value="1">One</option>
							<option value="2">Two</option>
							<option value="3">Three</option>
						</Form.Select>
					</Form.Group>

					<Form.Group>
						<Form.Label>Klassifisering</Form.Label>
						<Form.Select aria-label="Velg klassifisering" required>
							<option>Velg</option>
							<option value="1">One</option>
							<option value="2">Two</option>
							<option value="3">Three</option>
						</Form.Select>
					</Form.Group>
				</div>

				<div className={styles.actions}>
					<a href="/admin">Avbryt</a>

					<Button
						icon={<FontAwesomeIcon icon={faCheck} type="submit" />}>
						Last opp
					</Button>
				</div>
			</Form>
		</AdminLayout>
	);
}

Component.displayName = 'CreateSource';
