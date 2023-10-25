import Form from 'react-bootstrap/Form';
import Badge from 'react-bootstrap/Badge';
import InputGroup from 'react-bootstrap/InputGroup';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faMagnifyingGlass } from '@fortawesome/pro-regular-svg-icons';
import {
	faCloudArrowUp,
	faCog,
	faEye,
	faFilePdf,
	faGlobe,
	faTrash,
} from '@fortawesome/pro-solid-svg-icons';

import AdminLayout from '../../components/Layout/AdminLayout';
import Button from '../../components/Button/Button';

import styles from './Admin.module.css';
import { useNavigate } from 'react-router';

const data = [
	{
		type: 'PDF',
		name: 'Koronavirus - FHI',
		owner: 'FHI',
		classification: 'Offentlig',
		updated: '01.01.2021',
		id: '1',
		flagged: true,
	},
	{
		type: 'PDF',
		name: 'Bananaramalamadingdong',
		owner: 'NTE',
		classification: 'Offentlig',
		updated: '13.10.2020',
		id: '2',
		flagged: false,
	},
	{
		type: 'PDF',
		name: 'Koronavirus - FHI',
		owner: 'FHI',
		classification: 'Offentlig',
		updated: '01.01.2021',
		id: '3',
		flagged: false,
	},
	{
		type: 'web',
		name: 'Bananaramalamadingdong',
		owner: 'NTE',
		classification: 'Offentlig',
		updated: '13.10.2020',
		id: '4',
		flagged: false,
	},
];
export function Component(): JSX.Element {
	const navigate = useNavigate();

	const handleOpenItem = () => {
		console.log('open');
	};

	const handleEditItem = (id: string) => {
		navigate(`edit/${id}`);
	};

	const handleDeleteItem = () => {
		if (!confirm('Er du sikker på at du vil slette denne kilden?')) return;
	};

	return (
		<AdminLayout className={styles.layout}>
			<div className={styles.header}>
				<Button
					className={styles.button}
					icon={<FontAwesomeIcon icon={faCloudArrowUp} />}
					onClick={() => navigate('create')}>
					Legg til kilde
				</Button>
			</div>

			<div className={styles.filters}>
				<InputGroup className={styles.search}>
					<Form.Control placeholder="Søk etter kilde" />
					<InputGroup.Text>
						<FontAwesomeIcon icon={faMagnifyingGlass} />
					</InputGroup.Text>
				</InputGroup>

				<Form.Check
					className={styles.check}
					type="checkbox"
					label="Vis kun flagget"
				/>

				<Form.Check
					className={styles.check}
					type="switch"
					label="Vis PDF-kilder"
					defaultChecked={true}
				/>

				<Form.Check
					className={styles.check}
					type="switch"
					label="Vis web-kilder"
					defaultChecked={true}
				/>
			</div>

			<div className={styles.head}>
				<div className={styles.col} style={{ flex: 1 }}>
					Type
				</div>
				<div className={styles.col} style={{ flex: 5 }}>
					Navn
				</div>
				<div className={styles.col} style={{ flex: 3 }}>
					Eier
				</div>
				<div className={styles.col} style={{ flex: 2 }}>
					Klassifisering
				</div>
				<div className={styles.col} style={{ flex: 2 }}>
					Oppdatert
				</div>
				<div className={styles.col} style={{ flex: 2 }}>
					Handlinger
				</div>
			</div>

			<div className={styles.rows}>
				{data.map(item => (
					<div
						className={`${styles.row} ${
							item.flagged && styles.flagged
						}`}
						key={item.id}>
						<div className={styles.col} style={{ flex: 1 }}>
							<FontAwesomeIcon
								icon={
									item.type.includes('PDF')
										? faFilePdf
										: faGlobe
								}
							/>
						</div>

						<div className={styles.col} style={{ flex: 5 }}>
							{item.name}
						</div>

						<div className={styles.col} style={{ flex: 3 }}>
							{item.owner}
						</div>

						<div className={styles.col} style={{ flex: 2 }}>
							<Badge pill bg="primary">
								{item.classification}
							</Badge>
						</div>

						<div className={styles.col} style={{ flex: 2 }}>
							{item.updated}
						</div>

						<div
							className={`${styles.col} ${styles.actions}`}
							style={{ flex: 2 }}>
							<button
								className={styles.open}
								onClick={handleOpenItem}
								title="Åpne">
								<FontAwesomeIcon icon={faEye} />
							</button>

							<button
								className={styles.edit}
								onClick={() => handleEditItem(item.id)}
								title="Rediger">
								<FontAwesomeIcon icon={faCog} />
							</button>

							<button
								className={styles.delete}
								onClick={handleDeleteItem}
								title="Slett">
								<FontAwesomeIcon icon={faTrash} />
							</button>
						</div>
					</div>
				))}
			</div>

			<div className={styles.bottomActions}>
				<span>Viser {data.length} kilder</span>

				<Button
					className={styles.button}
					icon={<FontAwesomeIcon icon={faCloudArrowUp} />}
					onClick={() => navigate('create')}>
					Legg til kilde
				</Button>
			</div>
		</AdminLayout>
	);
}

Component.displayName = 'AdminPage';
