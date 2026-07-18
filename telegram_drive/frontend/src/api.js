import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({ baseURL: API_URL, withCredentials: true });
let csrfPromise = null;

const needsCsrf = (method) => ['post', 'put', 'patch', 'delete'].includes((method || 'get').toLowerCase());

const getCsrfToken = async () => {
  const existing = window.csrf_token || window.frappe?.csrf_token;
  if (existing && !String(existing).includes('{{')) return existing;
  if (!csrfPromise) {
    csrfPromise = axios
      .get(`${API_URL}/api/method/telegram_drive.api.auth.csrf`)
      .then((response) => response.data?.message?.csrf_token)
      .then((token) => {
        window.csrf_token = token;
        return token;
      });
  }
  return csrfPromise;
};

api.interceptors.request.use(async (config) => {
  const csrfToken = needsCsrf(config.method) ? await getCsrfToken() : (window.csrf_token || window.frappe?.csrf_token);
  if (csrfToken) {
    config.headers['X-Frappe-CSRF-Token'] = csrfToken;
  }
  const token = localStorage.getItem('td_token');
  if (token) config.headers['X-Token'] = token;
  const portalToken = localStorage.getItem('td_portal_token');
  if (portalToken) config.headers['X-Portal-Token'] = portalToken;
  return config;
});

const unwrap = (promise) => promise.then((response) => ({ ...response, data: response.data?.message ?? response.data }));
const method = (path) => `/api/method/${path}`;
const post = (path, data, config = {}) => unwrap(api.post(method(path), data, config));
const get = (path, config = {}) => unwrap(api.get(method(path), config));

export default api;

export const authStart = (data) => post('telegram_drive.api.auth.start', data, { headers: { 'Content-Type': 'multipart/form-data' } });
export const authCode = (data) => post('telegram_drive.api.auth.verify_code', data, { headers: { 'Content-Type': 'multipart/form-data' } });
export const authPassword = (data) => post('telegram_drive.api.auth.verify_password', data, { headers: { 'Content-Type': 'multipart/form-data' } });
export const authMe = () => get('telegram_drive.api.auth.me');
export const getSettings = () => get('telegram_drive.api.settings.get_settings');
export const updateSettings = (data) => post('telegram_drive.api.settings.update_settings', data, { headers: { 'Content-Type': 'multipart/form-data' } });
export const getStorageSummary = (folderId) => get('telegram_drive.api.settings.storage_summary', { params: { folder_id: folderId } });
export const getMyPermissions = () => get('telegram_drive.api.permissions.me');
export const getDriveUserPermissions = () => get('telegram_drive.api.permissions.list_users');
export const saveDriveUserPermission = (data) => post('telegram_drive.api.permissions.save_user', data, { headers: { 'Content-Type': 'multipart/form-data' } });
export const deleteDriveUserPermission = (user) => post('telegram_drive.api.permissions.delete_user', { user });

export const portalLogin = (data) => post('telegram_drive.api.portal.login', data, { headers: { 'Content-Type': 'multipart/form-data' } });
export const portalMe = () => get('telegram_drive.api.portal.me');
export const portalChangePassword = (data) => post('telegram_drive.api.portal.change_password', data, { headers: { 'Content-Type': 'multipart/form-data' } });
export const portalGetSettings = () => get('telegram_drive.api.portal.get_settings');
export const portalGetStorageSummary = (folderId) => get('telegram_drive.api.portal.storage_summary', { params: { folder_id: folderId } });
export const getPortalUsers = () => get('telegram_drive.api.portal.list_users');
export const createPortalUser = (data) => post('telegram_drive.api.portal.create_user', data, { headers: { 'Content-Type': 'multipart/form-data' } });
export const updatePortalUser = (id, data) => {
  data.append('username', data.get('username') || id);
  return post('telegram_drive.api.portal.update_user', data, { headers: { 'Content-Type': 'multipart/form-data' }, params: { username: id } });
};
export const deletePortalUser = (id) => post('telegram_drive.api.portal.delete_user', { username: id });

export const getFolders = (parentId) => get('telegram_drive.api.folders.list', { params: { parent_id: parentId } });
export const getAllFolders = () => get('telegram_drive.api.folders.list_all');
export const createFolder = (data) => post('telegram_drive.api.folders.create', data, { headers: { 'Content-Type': 'multipart/form-data' } });
export const deleteFolder = (id) => post('telegram_drive.api.folders.delete', { folder_id: id });

export const getFiles = (folderId) => get('telegram_drive.api.files.list', { params: { folder_id: folderId } });
export const uploadFile = (data, onProgress) => post('telegram_drive.api.files.upload', data, { headers: { 'Content-Type': 'multipart/form-data' }, onUploadProgress: onProgress });
export const uploadFileChunk = (data, onProgress) => post('telegram_drive.api.files.upload_chunk', data, { headers: { 'Content-Type': 'multipart/form-data' }, onUploadProgress: onProgress });
export const getUploadProgress = (uploadId) => get('telegram_drive.api.transfers.upload_progress', { params: { upload_id: uploadId } });
export const deleteFile = (id) => post('telegram_drive.api.files.delete', { file_id: id });
export const moveFile = (id, data) => post('telegram_drive.api.files.move', data, { headers: { 'Content-Type': 'multipart/form-data' }, params: { file_id: id } });
export const downloadFileUrl = (id) => {
  const token = localStorage.getItem('td_token');
  const query = new URLSearchParams({ file_id: id });
  if (token) query.set('token', token);
  return `${API_URL}/api/method/telegram_drive.api.files.download?${query.toString()}`;
};
export const createShareLink = (id) => post('telegram_drive.api.files.create_share_link', { file_id: id });
export const publicShareUrl = (path) => `${API_URL}${path}`;
export const getCloudNotes = () => get('telegram_drive.api.notes.list');
export const createCloudNote = (data) => post('telegram_drive.api.notes.create', data, { headers: { 'Content-Type': 'multipart/form-data' } });
export const updateCloudNote = (id, data) => post('telegram_drive.api.notes.update', data, { headers: { 'Content-Type': 'multipart/form-data' }, params: { note_id: id } });
export const deleteCloudNote = (id) => post('telegram_drive.api.notes.delete', { note_id: id });
export const startDownload = (id) => post('telegram_drive.api.files.start_download', { file_id: id });
export const getDownloadProgress = (downloadId) => get('telegram_drive.api.transfers.download_progress', { params: { download_id: downloadId } });
export const tempDownloadFileUrl = (downloadId) => {
  const token = localStorage.getItem('td_token');
  const query = new URLSearchParams({ download_id: downloadId });
  if (token) query.set('token', token);
  return `${API_URL}/api/method/telegram_drive.api.files.temp_download?${query.toString()}`;
};
export const listTempFiles = () => get('telegram_drive.api.transfers.list_temp_files');
export const deleteTempFile = (filename) => post('telegram_drive.api.transfers.delete_temp_file', { filename });

export const portalGetFolders = (parentId) => get('telegram_drive.api.portal.list_folders', { params: { parent_id: parentId } });
export const portalCreateFolder = (data) => post('telegram_drive.api.portal.create_folder', data, { headers: { 'Content-Type': 'multipart/form-data' } });
export const portalGetFiles = (folderId) => get('telegram_drive.api.portal.list_files', { params: { folder_id: folderId } });
export const portalCreateShareLink = (id) => post('telegram_drive.api.portal.create_share_link', { file_id: id });
export const portalUploadFile = (data, onProgress) => post('telegram_drive.api.portal.upload', data, { headers: { 'Content-Type': 'multipart/form-data' }, onUploadProgress: onProgress });
export const portalUploadFileChunk = (data, onProgress) => post('telegram_drive.api.portal.upload_chunk', data, { headers: { 'Content-Type': 'multipart/form-data' }, onUploadProgress: onProgress });
export const portalGetUploadProgress = (uploadId) => get('telegram_drive.api.portal.upload_progress', { params: { upload_id: uploadId } });
export const portalDownloadFileUrl = (id) => `${API_URL}/api/method/telegram_drive.api.portal.download?file_id=${encodeURIComponent(id)}&token=${localStorage.getItem('td_portal_token')}`;
export const portalStartDownload = (id) => post('telegram_drive.api.portal.start_download', { file_id: id });
export const portalGetDownloadProgress = (downloadId) => get('telegram_drive.api.portal.download_progress', { params: { download_id: downloadId } });
export const portalTempDownloadFileUrl = (downloadId) => `${API_URL}/api/method/telegram_drive.api.portal.temp_download?download_id=${encodeURIComponent(downloadId)}&token=${localStorage.getItem('td_portal_token')}`;
export const portalGetCloudNotes = () => get('telegram_drive.api.portal.list_notes');
export const portalCreateCloudNote = (data) => post('telegram_drive.api.portal.create_note', data, { headers: { 'Content-Type': 'multipart/form-data' } });
export const portalUpdateCloudNote = (id, data) => post('telegram_drive.api.portal.update_note', data, { headers: { 'Content-Type': 'multipart/form-data' }, params: { note_id: id } });
export const portalDeleteCloudNote = (id) => post('telegram_drive.api.portal.delete_note', { note_id: id });
