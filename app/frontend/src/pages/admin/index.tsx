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
import { Document } from '../../api';

interface Filters {
	search: string;
	flagged: boolean;
	pdf: boolean;
	web: boolean;
}
interface PaginateDocuments {
	documents: Document[];
	total: number;
}
export function Component(): JSX.Element {
	const [data, setData] = useState<PaginateDocuments>({
		documents: [],
		total: 0,
	});
	const [filters, setFilters] = useState<Filters>({
		search: '',
		flagged: false,
		pdf: true,
		web: true,
	});

	const updateFilters = (key: string, value: boolean | string) => {
		console.log('update filters');
		setFilters(prev => ({ ...prev, [key]: value }));
	};

	const navigate = useNavigate();

	useEffect(() => {
		getDocuments();
	}, [filters.flagged, filters.pdf, filters.web]);

	// get all documents from /documents
	async function getDocuments(): Promise<void> {
		setData({ documents: [], total: 0 });
		const query = new URLSearchParams(filters as any);

		fetch(`/api/documents/?${query}`)
			.then(res => res.json())
			.then(json => setData(json));
	}

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
					<Form.Control
						placeholder="Søk etter kilde"
						onChange={e => updateFilters('search', e.target.value)}
						onKeyUp={e => {
							if (e.key !== 'Enter') return;

							getDocuments();
						}}
					/>
					<InputGroup.Text>
						<FontAwesomeIcon icon={faMagnifyingGlass} />
					</InputGroup.Text>
				</InputGroup>

				<Form.Check
					className={styles.check}
					type="checkbox"
					label="Vis kun flagget"
					onChange={e => updateFilters('flagged', e.target.checked)}
				/>

				<Form.Check
					className={styles.check}
					type="switch"
					label="Vis PDF-kilder"
					defaultChecked={true}
					onChange={e => updateFilters('pdf', e.target.checked)}
				/>

				<Form.Check
					className={styles.check}
					type="switch"
					label="Vis web-kilder"
					defaultChecked={true}
					onChange={e => updateFilters('web', e.target.checked)}
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
				{data?.documents?.map(item => (
					<div
						className={`${styles.row} ${
							item.flagged && styles.flagged
						}`}
						key={item._id}>
						<div className={styles.col} style={{ flex: 1 }}>
							<FontAwesomeIcon
								icon={
									item?.type?.includes('file')
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
				<span>
					Viser {data?.documents?.length} kilder av {data.total}
				</span>

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
