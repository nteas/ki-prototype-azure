import { useNavigate } from 'react-router';
import { useEffect, useState } from 'react';
import Form from 'react-bootstrap/Form';
import Badge from 'react-bootstrap/Badge';
import InputGroup from 'react-bootstrap/InputGroup';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faMagnifyingGlass } from '@fortawesome/pro-regular-svg-icons';
import {
	faCaretUp,
	faCaretDown,
	faCloudArrowUp,
	faCog,
	faEye,
	faFilePdf,
	faGlobe,
	faTrash,
	faSpinnerThird,
} from '@fortawesome/pro-solid-svg-icons';

import AdminLayout from '../../components/Layout/AdminLayout';
import Button from '../../components/Button/Button';

import styles from './Admin.module.scss';
import { Document, apiFetch, classificationMap } from '../../api';
import DocModal from '../../components/Modal/DocModal';
import { formatDate, getOwner } from '../../libs/utils';

interface Filters {
	search: string;
	flagged: boolean;
	pdf: boolean;
	web: boolean;
	limit: number;
	order_by: string;
	order: string;
}
interface PaginateDocuments {
	documents: Document[];
	total: number;
}

const DEFAULT_LIMIT = 20;

export function Component(): JSX.Element {
	const [loading, setLoading] = useState<boolean>(true);
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
		limit: DEFAULT_LIMIT,
		order_by: 'updated_at',
		order: 'desc',
	});

	const filterKeys = [
		'type',
		'title',
		'owner',
		'classification',
		'updated_at',
	];

	const updateFilters = (key: string, value?: boolean | string | number) => {
		console.log('update filters');

		if (filterKeys.includes(key)) {
			const order =
				filters.order_by !== key
					? 'asc'
					: filters.order === 'asc'
					? 'desc'
					: 'asc';
			setFilters(prev => ({ ...prev, order_by: key, order }));
			return;
		}

		setFilters(prev => ({ ...prev, [key]: value }));
	};

	const navigate = useNavigate();

	useEffect(() => {
		getDocuments();
	}, [
		filters.flagged,
		filters.pdf,
		filters.web,
		filters.limit,
		filters.order_by,
		filters.order,
	]);

	// get all documents from /documents
	async function getDocuments(): Promise<void> {
		setLoading(true);
		const query = new URLSearchParams(filters as any);

		apiFetch(`/api/documents/?${query}`)
			.then(res => res.json())
			.then(json => setData(json))
			.then(() => setLoading(false));
	}

	const handleEditItem = (id: string) => {
		navigate(`edit/${id}`);
	};

	const handleDeleteItem = (id: string) => {
		if (!confirm('Er du sikker på at du vil slette denne kilden?')) return;

		setLoading(true);

		apiFetch(`/api/documents/${id}`, { method: 'DELETE' }).then(() => {
			getDocuments();
		});
	};

	return (
		<AdminLayout className={styles.layout} loading={loading}>
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
					onClick={() => updateFilters('type')}
					className={`${styles.col} ${styles.orderHead}`}
					style={{ flex: 1 }}>
					Type
					{filters.order_by === 'type' && (
						<span className={styles.orderButton}>
							<FontAwesomeIcon
								icon={
									filters.order === 'desc'
										? faCaretDown
										: faCaretUp
								}
							/>
						</span>
					)}
				</div>
				<div
					onClick={() => updateFilters('title')}
					className={`${styles.col} ${styles.orderHead}`}
					style={{ flex: 5 }}>
					Tittel
					{filters.order_by === 'title' && (
						<span className={styles.orderButton}>
							<FontAwesomeIcon
								icon={
									filters.order === 'desc'
										? faCaretDown
										: faCaretUp
								}
							/>
						</span>
					)}
				</div>
				<div
					onClick={() => updateFilters('owner')}
					className={`${styles.col} ${styles.orderHead}`}
					style={{ flex: 3 }}>
					Eier
					{filters.order_by === 'owner' && (
						<span className={styles.orderButton}>
							<FontAwesomeIcon
								icon={
									filters.order === 'desc'
										? faCaretDown
										: faCaretUp
								}
							/>
						</span>
					)}
				</div>
				<div
					onClick={() => updateFilters('classification')}
					className={`${styles.col} ${styles.orderHead}`}
					style={{ flex: 2 }}>
					Klassifisering
					{filters.order_by === 'classification' && (
						<span className={styles.orderButton}>
							<FontAwesomeIcon
								icon={
									filters.order === 'desc'
										? faCaretDown
										: faCaretUp
								}
							/>
						</span>
					)}
				</div>
				<div
					className={`${styles.col} ${styles.orderHead}`}
					style={{ flex: 2 }}
					onClick={() => updateFilters('updated_at')}>
					Oppdatert
					{filters.order_by === 'updated_at' && (
						<span className={styles.orderButton}>
							<FontAwesomeIcon
								icon={
									filters.order === 'desc'
										? faCaretDown
										: faCaretUp
								}
							/>
						</span>
					)}
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
					<ItemRow
						key={item.id}
						item={item}
						setViewDocument={() => setViewDocument(item)}
						handleEditItem={() => handleEditItem(item.id)}
						handleDeleteItem={() => handleDeleteItem(item.id)}
					/>
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
								updateFilters(
									'limit',
									filters.limit + DEFAULT_LIMIT
								)
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

interface ItemRowProps {
	item: Document;
	setViewDocument: () => void;
	handleEditItem: () => void;
	handleDeleteItem: () => void;
}

function ItemRow({
	item,
	setViewDocument,
	handleEditItem,
	handleDeleteItem,
}: ItemRowProps) {
	const [status, setStatus] = useState<string>(item?.status || 'done');

	useEffect(() => {
		if (item.status !== 'processing') return;
		const sse = new EventSource(`/api/documents/status/${item.id}`);

		sse.onmessage = e => {
			if (e.data !== 'processing') {
				console.log('item processing');
				setStatus(e.data);
				return;
			}
		};
		sse.onerror = () => {
			console.log('event disconnect');
			sse.close();
		};
		return () => {
			console.log('event disconnect');
			sse.close();
		};
	}, []);

	return (
		<div
			className={`${styles.row} ${
				item?.flagged_pages?.length > 0 && styles.flagged
			}`}
			key={item.id}>
			<div className={styles.col} style={{ flex: 1 }}>
				<FontAwesomeIcon
					icon={item?.type?.includes('pdf') ? faFilePdf : faGlobe}
				/>
			</div>

			<div
				className={styles.col}
				style={{ flex: 5, cursor: 'pointer' }}
				onClick={handleEditItem}>
				{item.title}
			</div>

			<div className={styles.col} style={{ flex: 3 }}>
				{getOwner(item.owner ?? '').split(':')[0]}
			</div>

			<div className={styles.col} style={{ flex: 2 }}>
				<Badge
					pill
					bg="primary"
					className={styles[item?.classification || '']}>
					{item.classification &&
						classificationMap[item.classification]}
				</Badge>
			</div>

			<div className={styles.col} style={{ flex: 2 }}>
				{formatDate(item.updated_at)}
			</div>

			<div
				className={`${styles.col} ${styles.actions}`}
				style={{ flex: 2 }}>
				{status === 'processing' ? (
					<div className={styles.spinner}>
						<FontAwesomeIcon icon={faSpinnerThird} />
					</div>
				) : (
					<>
						<button
							className={styles.open}
							onClick={() => {
								if (item?.type?.includes('pdf')) {
									setViewDocument();
									return;
								}

								window.open(item.url, '_blank');
							}}
							title="Åpne">
							<FontAwesomeIcon icon={faEye} />
						</button>

						<button
							className={styles.edit}
							onClick={handleEditItem}
							title="Rediger">
							<FontAwesomeIcon icon={faCog} />
						</button>

						<button
							className={styles.delete}
							onClick={handleDeleteItem}
							title="Slett">
							<FontAwesomeIcon icon={faTrash} />
						</button>
					</>
				)}
			</div>
		</div>
	);
}
