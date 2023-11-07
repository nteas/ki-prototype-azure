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
import { Document, ClassificationEnum } from '../../api';
import { Modal } from '../../components/Modal/Modal';

// classification map
const classificationMap = {
	[ClassificationEnum.public]: 'Åpen',
	[ClassificationEnum.internal]: 'Intern',
	[ClassificationEnum.confidential]: 'Konfidensiell',
	[ClassificationEnum.powerSensitive]: 'Kraftsensitiv',
};
interface Filters {
	search: string;
	flagged: boolean;
	pdf: boolean;
	web: boolean;
	limit: number;
}
interface PaginateDocuments {
	documents: Document[];
	total: number;
}

export function Component(): JSX.Element {
	const [viewDocument, setViewDocument] = useState<Document | null>(null);

	const [data, setData] = useState<PaginateDocuments>({
		documents: [],
		total: 0,
	});
	const [filters, setFilters] = useState<Filters>({
		search: '',
		flagged: false,
		pdf: true,
		web: true,
		limit: 10,
	});

	const updateFilters = (key: string, value: boolean | string | number) => {
		console.log('update filters');
		setFilters(prev => ({ ...prev, [key]: value }));
	};

	const navigate = useNavigate();

	useEffect(() => {
		getDocuments();
	}, [filters.flagged, filters.pdf, filters.web, filters.limit]);

	// get all documents from /documents
	async function getDocuments(): Promise<void> {
		const query = new URLSearchParams(filters as any);

		fetch(`/api/documents/?${query}`)
			.then(res => res.json())
			.then(json => setData(json));
	}

	const handleEditItem = (id: string) => {
		navigate(`edit/${id}`);
	};

	const handleDeleteItem = (id: string) => {
		if (!confirm('Er du sikker på at du vil slette denne kilden?')) return;

		fetch(`/api/documents/?${id}`).then(() => {
			getDocuments();
		});
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
				<div
					onClick={() => console.log('ordering')}
					className={styles.col}
					style={{ flex: 1 }}>
					Type
				</div>
				<div
					onClick={() => console.log('ordering')}
					className={styles.col}
					style={{ flex: 5 }}>
					Tittel
				</div>
				<div
					onClick={() => console.log('ordering')}
					className={styles.col}
					style={{ flex: 3 }}>
					Eier
				</div>
				<div
					onClick={() => console.log('ordering')}
					className={styles.col}
					style={{ flex: 2 }}>
					Klassifisering
				</div>
				<div
					onClick={() => console.log('ordering')}
					className={styles.col}
					style={{ flex: 2 }}>
					Oppdatert
				</div>
				<div
					onClick={() => console.log('ordering')}
					className={styles.col}
					style={{ flex: 2 }}>
					Handlinger
				</div>
			</div>

			<div className={styles.rows}>
				{data?.documents?.map(item => (
					<div
						className={`${styles.row} ${
							item.flagged && styles.flagged
						}`}
						key={item.id}>
						<div className={styles.col} style={{ flex: 1 }}>
							<FontAwesomeIcon
								icon={
									item?.type?.includes('pdf')
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
								{item.classification &&
									classificationMap[item.classification]}
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
								onClick={() => setViewDocument(item)}
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
								onClick={() => handleDeleteItem(item.id)}
								title="Slett">
								<FontAwesomeIcon icon={faTrash} />
							</button>
						</div>
					</div>
				))}
			</div>

			<div className={styles.bottomActions}>
				<div
					style={{
						display: 'flex',
						alignItems: 'center',
						gap: '10px',
					}}>
					Viser {data?.documents?.length} kilder av {data.total}
					{data?.documents?.length < data?.total && (
						<Button
							onClick={() =>
								updateFilters('limit', filters.limit + 10)
							}>
							Last flere
						</Button>
					)}
				</div>

				<Button
					className={styles.button}
					icon={<FontAwesomeIcon icon={faCloudArrowUp} />}
					onClick={() => navigate('create')}>
					Legg til kilde
				</Button>
			</div>

			{viewDocument && (
				<DocModal
					onClose={() => setViewDocument(null)}
					document={viewDocument}
				/>
			)}
		</AdminLayout>
	);
}

const DocModal = ({
	document,
	onClose,
}: {
	document: Document;
	onClose: () => void;
}) => {
	const [file, setFile] = useState<string | null>(null);

	return (
		<Modal onClose={onClose} title={document.title}>
			<div className={styles.docList}>
				{document?.file_pages
					?.sort((a: string, b: string) => a.localeCompare(b))
					.map((page, i) => (
						<Button key={i} onClick={() => setFile(page)}>
							{page}
						</Button>
					))}
			</div>

			{file && (
				<iframe
					className={styles.iframe}
					src={`/api/content/${file}`}
				/>
			)}
		</Modal>
	);
};
