import { useNavigate } from 'react-router';
import { useEffect, useState } from 'react';
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
import { getDocuments } from '../../api';
import { Document } from '../../api/models';

export function Component(): JSX.Element {
	const [data, setData] = useState<Document[]>([]);
	const navigate = useNavigate();

	// get data from api
	useEffect(() => {
		// fetch data
		getDocuments().then(documents => {
			console.log(documents);
			setData(documents);
		});
	}, []);

	const handleOpenItem = () => {
		console.log('open');
	};

	const handleEditItem = (_id: string) => {
		navigate(`edit/${_id}`);
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
					Tittel
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
				{data?.map(item => (
					<div
						className={`${styles.row} ${
							item.flagged && styles.flagged
						}`}
						key={item._id}>
						<div className={styles.col} style={{ flex: 1 }}>
							<FontAwesomeIcon
								icon={
									item?.type?.includes('PDF')
										? faFilePdf
										: faGlobe
								}
							/>
						</div>

						<div className={styles.col} style={{ flex: 5 }}>
							{item.title}
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
							{item.updated_at}
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
								onClick={() => handleEditItem(item._id)}
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
