# Reports Management Routes
# Add these routes to routes.py at the end of the file

def get_file_category(filename, content_type):
    """Determine file category based on extension and content type."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    content_type_lower = (content_type or '').lower()

    # Map extensions and MIME types to categories
    if ext in ['pdf'] or 'pdf' in content_type_lower:
        return 'pdf'
    elif ext in ['csv'] or 'csv' in content_type_lower:
        return 'csv'
    elif ext in ['xlsx', 'xls'] or 'spreadsheet' in content_type_lower or 'excel' in content_type_lower:
        return 'excel'
    elif ext in ['docx', 'doc'] or 'word' in content_type_lower:
        return 'word'
    elif ext in ['pptx', 'ppt'] or 'presentation' in content_type_lower:
        return 'ppt'
    elif ext in ['txt'] or 'text' in content_type_lower:
        return 'text'
    elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp'] or 'image' in content_type_lower:
        return 'image'
    else:
        return 'other'


@app.route('/reports-management')
@login_required
def reports_management():
    """Main reports management page (accessible to admin and interns)."""
    if current_user.role not in ['admin', 'intern']:
        abort(403)

    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', '')
    uploader_filter = request.args.get('uploader', type=int)
    search_query = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    # Build base query
    query = ReportFile.query

    # Filter by role: admins see all, interns/users see only their own and team reports
    if current_user.role == 'admin':
        # Admin sees all reports
        pass
    elif current_user.role == 'intern':
        # Intern sees only their own reports
        query = query.filter_by(uploaded_by_id=current_user.id)

    # Apply filters
    if category_filter:
        query = query.filter_by(file_type=category_filter)
    if uploader_filter and current_user.role == 'admin':
        query = query.filter_by(uploaded_by_id=uploader_filter)
    if search_query:
        query = query.filter(ReportFile.original_filename.ilike(f'%{search_query}%'))
    if date_from:
        try:
            start_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(ReportFile.uploaded_at >= start_date)
        except ValueError:
            pass
    if date_to:
        try:
            end_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(ReportFile.uploaded_at < end_date)
        except ValueError:
            pass

    # Order by most recent first
    reports = query.order_by(ReportFile.uploaded_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    # Get unique file types and uploaders for filter dropdowns
    all_categories = db.session.query(ReportFile.file_type).distinct().all()
    categories = [c[0] for c in all_categories if c[0]]

    all_uploaders = []
    if current_user.role == 'admin':
        all_uploaders = User.query.filter(User.role.in_(['admin', 'intern'])).order_by(User.full_name).all()

    return render_template('reports_management.html',
                         reports=reports,
                         categories=categories,
                         all_uploaders=all_uploaders,
                         category_filter=category_filter,
                         uploader_filter=uploader_filter,
                         search_query=search_query,
                         date_from=date_from,
                         date_to=date_to)


@app.route('/report/upload', methods=['POST'])
@login_required
def upload_report():
    """Upload a new report file."""
    if current_user.role not in ['admin', 'intern']:
        abort(403)

    if 'file' not in request.files:
        flash('No file part in request', 'danger')
        return redirect(url_for('reports_management'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('reports_management'))

    # description removed; use `category` (system category) instead
    category = request.form.get('category', '')

    try:
        filename = secure_filename(file.filename)
        if not filename:
            flash('Invalid filename', 'danger')
            return redirect(url_for('reports_management'))

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        # Save file
        file.save(file_path)
        file_size = os.path.getsize(file_path)

        # Determine file type
        file_type = get_file_category(filename, file.content_type)

        # Create report record
        report = ReportFile(
            filename=unique_filename,
            original_filename=filename,
            file_size=file_size,
            content_type=file.content_type or 'application/octet-stream',
            file_type=file_type,
            category=category,
            uploaded_by_id=current_user.id
        )
        db.session.add(report)
        db.session.commit()

        # Success message suppressed to avoid popup after upload

    except Exception as e:
        db.session.rollback()
        flash(f'Error uploading file: {str(e)}', 'danger')

    return redirect(url_for('reports_management', no_flash=1))


@app.route('/report/<int:report_id>/download')
@login_required
def download_report(report_id):
    """Download a report file."""
    report = ReportFile.query.get_or_404(report_id)

    # Permission check
    if current_user.role == 'intern' and report.uploaded_by_id != current_user.id:
        abort(403)

    # Log download
    print(f"DEBUG: User {current_user.username} downloading report {report.id}: {report.original_filename}")

    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], report.filename, as_attachment=True, download_name=report.original_filename)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'danger')
        return redirect(url_for('reports_management'))


@app.route('/report/<int:report_id>/delete', methods=['POST'])
@login_required
def delete_report(report_id):
    """Delete a report file (admin only or by uploader)."""
    report = ReportFile.query.get_or_404(report_id)

    # Permission check: only admin or the uploader can delete
    if current_user.role != 'admin' and report.uploaded_by_id != current_user.id:
        abort(403)

    try:
        # Delete file from disk
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], report.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete database record
        db.session.delete(report)
        db.session.commit()

        # Success message suppressed to avoid popup after delete

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting report: {str(e)}', 'danger')

    return redirect(url_for('reports_management', no_flash=1))


@app.route('/api/reports/stats')
@login_required
def api_reports_stats():
    """Get statistics about uploaded reports (for admin dashboard)."""
    if current_user.role != 'admin':
        abort(403)

    # Total reports
    total_reports = ReportFile.query.count()

    # Reports by file type
    category_stats = db.session.query(
        ReportFile.file_type,
        func.count(ReportFile.id).label('count')
    ).group_by(ReportFile.file_type).all()

    # Reports by uploader
    uploader_stats = db.session.query(
        User.full_name,
        func.count(ReportFile.id).label('count')
    ).join(ReportFile, User.id == ReportFile.uploaded_by_id).group_by(User.id, User.full_name).all()

    # Total file size
    total_size = db.session.query(func.sum(ReportFile.file_size)).scalar() or 0

    return jsonify({
        'total_reports': total_reports,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'category_stats': [{'category': c[0], 'count': c[1]} for c in category_stats],
        'uploader_stats': [{'uploader': u[0], 'count': u[1]} for u in uploader_stats]
    })
