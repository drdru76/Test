from flask import Blueprint, render_template, abort, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User, Decision, Option, Suggestion, Clarification, UserAction
from app.forms import DecisionForm, OptionForm, SuggestionForm, ClarificationForm, EditProfileForm
from app.utils import categorize_decision
import json

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
def index():
    selected_category = request.args.get('category')
    categories = db.session.query(Decision.category).filter(Decision.category != None).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    if current_user.is_authenticated:
        user_query = current_user.decisions
        public_query = Decision.query.filter(Decision.is_public == True, Decision.user_id != current_user.id)
        
        # Check for pending actions on current user's decisions
        pending_suggestions = Suggestion.query.join(Decision).filter(
            Decision.user_id == current_user.id,
            Suggestion.status == 'pending'
        ).count()
        
        pending_clarifications = Clarification.query.join(Decision).filter(
            Decision.user_id == current_user.id,
            Clarification.status == 'pending'
        ).count()
        
        if selected_category:
            user_query = user_query.filter(Decision.category == selected_category)
            public_query = public_query.filter(Decision.category == selected_category)
            
        user_decisions = user_query.order_by(Decision.created_at.desc()).all()
        public_decisions = public_query.order_by(Decision.created_at.desc()).all()
        
        return render_template('index.html', title='Home', decisions=user_decisions, 
                               public_decisions=public_decisions, categories=categories,
                               selected_category=selected_category,
                               pending_suggestions=pending_suggestions,
                               pending_clarifications=pending_clarifications)
    
    # For non-authenticated users, we show public decisions
    public_query = Decision.query.filter(Decision.is_public == True)
    if selected_category:
        public_query = public_query.filter(Decision.category == selected_category)
    
    public_decisions = public_query.order_by(Decision.created_at.desc()).all()
        
    return render_template('index.html', title='Home', categories=categories, 
                           public_decisions=public_decisions, selected_category=selected_category)

@bp.route('/decision/new', methods=['GET', 'POST'])
@login_required
def new_decision():
    form = DecisionForm()
    if form.validate_on_submit():
        decision = Decision(title=form.title.data, description=form.description.data, 
                            deadline=form.deadline.data, is_public=form.is_public.data, 
                            owner=current_user)
        
        # Categorize decision using AI
        decision.category = categorize_decision(decision)
        
        db.session.add(decision)
        db.session.commit()
        
        # Log action
        action = UserAction(user_id=current_user.id, action_type='asked', decision_id=decision.id)
        db.session.add(action)
        db.session.commit()

        flash('Your decision process has been started!')
        return redirect(url_for('main.view_decision', id=decision.id))
    return render_template('create_decision.html', title='New Decision', form=form)

@bp.route('/decision/<int:id>')
def view_decision(id):
    decision = Decision.query.get_or_404(id)
    if not decision.is_public:
        if current_user.is_anonymous or decision.owner != current_user:
            abort(403)
    
    # Log read action for authenticated users
    if current_user.is_authenticated:
        action = UserAction(user_id=current_user.id, action_type='read', decision_id=decision.id)
        db.session.add(action)
        db.session.commit()

    option_form = OptionForm()
    suggestion_form = SuggestionForm()
    clarification_form = ClarificationForm()
    return render_template('view_decision.html', title=decision.title, 
                           decision=decision, option_form=option_form, 
                           suggestion_form=suggestion_form,
                           clarification_form=clarification_form)

@bp.route('/decision/<int:id>/suggest_options')
@login_required
def suggest_options(id):
    decision = Decision.query.get_or_404(id)
    if decision.owner != current_user:
        abort(403)
    
    api_key = current_app.config.get('AI_API_KEY')
    provider = current_app.config.get('AI_PROVIDER')
    base_url = current_app.config.get('AI_BASE_URL')

    if api_key:
        try:
            if provider in ['openai', 'grok', 'groq']:
                from openai import OpenAI
                client = OpenAI(api_key=api_key, base_url=base_url)
                
                model = "gpt-3.5-turbo"
                if provider == 'grok':
                    model = "grok-2-1212"
                elif provider == 'groq':
                    model = "llama-3.3-70b-versatile"
                
                prompt = f"""
                As an expert decision-making assistant, provide 3 creative and distinct alternative options for the following decision.
                Base your suggestions heavily on both the title and the detailed description provided to ensure they are highly relevant.
                
                Decision Title: {decision.title}
                Decision Description: {decision.description}
                
                IMPORTANT: You must respond ONLY with a JSON object in the following format:
                {{
                  "suggestions": [
                    {{
                      "title": "string",
                      "description": "string",
                      "pros": "string",
                      "cons": "string"
                    }}
                  ]
                }}
                """
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={ "type": "json_object" }
                )
                content = response.choices[0].message.content
                data = json.loads(content)
                suggestions = data.get('suggestions', [])
                # If the AI didn't nest it under 'suggestions', but returned the list directly (unlikely with json_object mode but safe to check)
                if not suggestions and isinstance(data, list):
                    suggestions = data
                return jsonify({"suggestions": suggestions})
        except Exception as e:
            print(f"AI Error: {e}")
            # Fallback to simulation if AI fails
    
    # Simulation/Fallback
    title = decision.title.lower()
    description = (decision.description or "").lower()
    full_text = f"{title} {description}"
    
    # Simple rule-based "AI" for demonstration
    suggestions = []
    if "car" in full_text or "vehicle" in full_text:
        suggestions = [
            {"title": "Buy a used hybrid", "description": "Economical and environmentally friendly.", "pros": "Low fuel cost, reliable", "cons": "Higher initial cost than gas cars"},
            {"title": "Lease a new electric car", "description": "Experience the latest technology with lower monthly payments.", "pros": "Newest features, no maintenance worries", "cons": "Never own the asset, mileage limits"},
            {"title": "Public transport + Car sharing", "description": "Use trains/buses and rent a car only when needed.", "pros": "Cheapest option, no parking issues", "cons": "Less convenient, dependent on schedules"}
        ]
    elif "job" in full_text or "career" in full_text or "work" in full_text:
        suggestions = [
            {"title": "Upskill and stay", "description": "Take courses to qualify for a promotion in your current company.", "pros": "Stability, known environment", "cons": "Might not solve cultural issues"},
            {"title": "Freelance/Consulting", "description": "Start your own business using your current expertise.", "pros": "Flexibility, higher potential income", "cons": "Income instability, no benefits"},
            {"title": "Relocate for a new role", "description": "Apply for positions in cities with better industry growth.", "pros": "Fresh start, better opportunities", "cons": "Moving costs, away from friends/family"}
        ]
    elif "vacation" in full_text or "travel" in full_text or "trip" in full_text:
        suggestions = [
            {"title": "Staycation with local experiences", "description": "Explore hidden gems in your own city/state.", "pros": "Very low cost, zero travel stress", "cons": "Might not feel like a 'real' break"},
            {"title": "All-inclusive resort", "description": "Stress-free planning where everything is provided.", "pros": "Predictable budget, complete relaxation", "cons": "Less authentic local experience"},
            {"title": "Backpacking adventure", "description": "Move between multiple locations with a flexible itinerary.", "pros": "Exciting, many experiences", "cons": "Physically demanding, less comfort"}
        ]
    else:
        suggestions = [
            {"title": "Seek expert consultation", "description": "Talk to a specialist in this specific field for advice.", "pros": "Professional insight", "cons": "Can be expensive"},
            {"title": "Delay the decision", "description": "Wait for more information or for the situation to stabilize.", "pros": "Reduced uncertainty", "cons": "Opportunity cost of waiting"},
            {"title": "The 'Minimum Viable' approach", "description": "Try the smallest, least risky version of your best option first.", "pros": "Low risk, fast learning", "cons": "Might not show full potential"}
        ]
        
    return jsonify({"suggestions": suggestions})

@bp.route('/decision/<int:id>/refine_option', methods=['POST'])
@login_required
def refine_option(id):
    decision = Decision.query.get_or_404(id)
    if decision.owner != current_user:
        abort(403)
    
    data = request.get_json()
    option_title = data.get('title')
    
    if not option_title:
        return jsonify({"error": "No title provided"}), 400

    api_key = current_app.config.get('AI_API_KEY')
    provider = current_app.config.get('AI_PROVIDER')
    base_url = current_app.config.get('AI_BASE_URL')

    if api_key:
        try:
            if provider in ['openai', 'grok', 'groq']:
                from openai import OpenAI
                client = OpenAI(api_key=api_key, base_url=base_url)
                
                model = "gpt-3.5-turbo"
                if provider == 'grok':
                    model = "grok-2-1212"
                elif provider == 'groq':
                    model = "llama-3.3-70b-versatile"
                
                prompt = f"""
                As an expert decision-making assistant, help me flesh out an option for the following decision.
                
                Decision Title: {decision.title}
                Decision Description: {decision.description}
                
                Option Title: {option_title}
                
                Please provide a detailed description, pros, and cons for this specific option, considering the context of the decision.
                
                IMPORTANT: You must respond ONLY with a JSON object in the following format:
                {{
                  "description": "string",
                  "pros": "string",
                  "cons": "string"
                }}
                """
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={ "type": "json_object" }
                )
                content = response.choices[0].message.content
                suggestion = json.loads(content)
                return jsonify(suggestion)
        except Exception as e:
            print(f"AI Error: {e}")
            
    # Fallback/Dummy response
    return jsonify({
        "description": f"Details about {option_title} specifically for '{decision.title}'.",
        "pros": "Relevant to the decision context",
        "cons": "Needs further evaluation"
    })

@bp.route('/decision/<int:id>/clarify_description', methods=['POST'])
@login_required
def clarify_description(id):
    decision = Decision.query.get_or_404(id)
    if decision.owner != current_user:
        abort(403)
    
    data = request.get_json()
    current_title = data.get('title')
    current_description = data.get('description')
    
    api_key = current_app.config.get('AI_API_KEY')
    provider = current_app.config.get('AI_PROVIDER')
    base_url = current_app.config.get('AI_BASE_URL')

    if api_key:
        try:
            if provider in ['openai', 'grok', 'groq']:
                from openai import OpenAI
                client = OpenAI(api_key=api_key, base_url=base_url)
                
                model = "gpt-3.5-turbo"
                if provider == 'grok':
                    model = "grok-2-1212"
                elif provider == 'groq':
                    model = "llama-3.3-70b-versatile"
                
                prompt = f"""
                As an expert decision-making consultant, help me clarify and improve the description of a decision I'm trying to make.
                
                Current Title: {current_title}
                Current Description: {current_description}
                
                Please rewrite the description to be more clear, professional, and actionable. 
                Keep the core intent but improve the structure and wording. 
                If the current description is very short, expand on what might be important to consider.
                
                IMPORTANT: You must respond ONLY with a JSON object in the following format:
                {{
                  "clarified_description": "string (can contain basic HTML like <p>, <ul>, <li>, <strong>, <em>)"
                }}
                """
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={ "type": "json_object" }
                )
                content = response.choices[0].message.content
                result = json.loads(content)
                return jsonify(result)
        except Exception as e:
            print(f"AI Error: {e}")
            
    # Fallback response
    return jsonify({
        "clarified_description": f"<p>{current_description}</p><p><em>(Note: AI clarification unavailable. Consider adding more context about the goals, constraints, and stakeholders involved in this decision.)</em></p>"
    })

@bp.route('/decision/<int:id>/add_option', methods=['POST'])
@login_required
def add_option(id):
    decision = Decision.query.get_or_404(id)
    if decision.owner != current_user:
        abort(403)
    form = OptionForm()
    if form.validate_on_submit():
        option = Option(title=form.title.data, description=form.description.data,
                        pros=form.pros.data, cons=form.cons.data, decision=decision)
        db.session.add(option)
        db.session.commit()
        flash('Option added!')
    return redirect(url_for('main.view_decision', id=id))

@bp.route('/option/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_option(id):
    option = Option.query.get_or_404(id)
    if option.decision.owner != current_user and not current_user.is_admin:
        abort(403)
    form = OptionForm()
    if form.validate_on_submit():
        option.title = form.title.data
        option.description = form.description.data
        option.pros = form.pros.data
        option.cons = form.cons.data
        db.session.commit()
        flash('Option updated!')
        return redirect(url_for('main.view_decision', id=option.decision_id))
    elif request.method == 'GET':
        form.title.data = option.title
        form.description.data = option.description
        form.pros.data = option.pros
        form.cons.data = option.cons
    return render_template('edit_option.html', title='Edit Option', 
                           form=form, option=option)

@bp.route('/option/<int:id>/delete', methods=['POST'])
@login_required
def delete_option(id):
    option = Option.query.get_or_404(id)
    decision_id = option.decision_id
    if option.decision.owner != current_user and not current_user.is_admin:
        abort(403)
    db.session.delete(option)
    db.session.commit()
    flash('Option deleted!')
    return redirect(url_for('main.view_decision', id=decision_id))

@bp.route('/decision/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_decision(id):
    decision = Decision.query.get_or_404(id)
    if decision.owner != current_user and not current_user.is_admin:
        abort(403)
    form = DecisionForm()
    if form.validate_on_submit():
        decision.title = form.title.data
        decision.description = form.description.data
        decision.deadline = form.deadline.data
        decision.is_public = form.is_public.data
        db.session.commit()
        flash('Decision updated!')
        return redirect(url_for('main.view_decision', id=decision.id))
    elif request.method == 'GET':
        form.title.data = decision.title
        form.description.data = decision.description
        form.deadline.data = decision.deadline
        form.is_public.data = decision.is_public
    return render_template('edit_decision.html', title='Edit Decision', 
                           form=form, decision=decision)

@bp.route('/decision/<int:id>/delete', methods=['POST'])
@login_required
def delete_decision(id):
    decision = Decision.query.get_or_404(id)
    if decision.owner != current_user and not current_user.is_admin:
        abort(403)
    db.session.delete(decision)
    db.session.commit()
    flash('Decision deleted!')
    
    # If admin deleted from admin page, stay there
    next_page = request.args.get('next')
    if next_page:
        return redirect(next_page)
    return redirect(url_for('main.index'))

@bp.route('/admin/decisions/bulk_delete', methods=['POST'])
@login_required
def bulk_delete_decisions():
    if not current_user.is_admin:
        abort(403)
    
    decision_ids = request.form.getlist('decision_ids')
    if not decision_ids:
        flash('No decisions selected for deletion.')
        return redirect(url_for('main.admin'))
    
    count = 0
    for d_id in decision_ids:
        decision = Decision.query.get(int(d_id))
        if decision:
            db.session.delete(decision)
            count += 1
    
    if count > 0:
        db.session.commit()
        flash(f'Successfully deleted {count} decisions.')
    else:
        flash('No decisions were deleted.')
        
    return redirect(url_for('main.admin'))

@bp.route('/decision/<int:id>/add_suggestion', methods=['POST'])
@login_required
def add_suggestion(id):
    decision = Decision.query.get_or_404(id)
    if decision.owner == current_user or not decision.is_public:
        flash('You cannot suggest for this decision.')
        return redirect(url_for('main.view_decision', id=id))
    
    form = SuggestionForm()
    if form.validate_on_submit():
        suggestion = Suggestion(
            title=form.title.data,
            description=form.description.data,
            pros=form.pros.data,
            cons=form.cons.data,
            author=current_user,
            decision=decision
        )
        db.session.add(suggestion)
        db.session.commit()

        # Log action
        action = UserAction(user_id=current_user.id, action_type='suggestion', decision_id=decision.id)
        db.session.add(action)
        db.session.commit()

        flash('Suggestion submitted! The owner will review it.')
    return redirect(url_for('main.view_decision', id=id))

@bp.route('/suggestion/<int:id>/accept', methods=['POST'])
@login_required
def accept_suggestion(id):
    suggestion = Suggestion.query.get_or_404(id)
    if suggestion.decision.owner != current_user and not current_user.is_admin:
        abort(403)
    
    # Create an option from the suggestion
    option = Option(
        title=suggestion.title,
        description=suggestion.description,
        pros=suggestion.pros,
        cons=suggestion.cons,
        decision=suggestion.decision
    )
    db.session.add(option)
    suggestion.status = 'accepted'
    db.session.commit()
    flash('Suggestion accepted and added as an option!')
    return redirect(url_for('main.view_decision', id=suggestion.decision_id))

@bp.route('/suggestion/<int:id>/ignore', methods=['POST'])
@login_required
def ignore_suggestion(id):
    suggestion = Suggestion.query.get_or_404(id)
    if suggestion.decision.owner != current_user and not current_user.is_admin:
        abort(403)
    
    suggestion.status = 'ignored'
    db.session.commit()
    flash('Suggestion ignored.')
    return redirect(url_for('main.view_decision', id=suggestion.decision_id))

@bp.route('/decision/<int:id>/add_clarification', methods=['POST'])
@login_required
def add_clarification(id):
    decision = Decision.query.get_or_404(id)
    if decision.owner == current_user or not decision.is_public:
        flash('You cannot request clarification for this decision.')
        return redirect(url_for('main.view_decision', id=id))
    
    form = ClarificationForm()
    if form.validate_on_submit():
        clarification = Clarification(
            message=form.message.data,
            author=current_user,
            decision=decision
        )
        db.session.add(clarification)
        db.session.commit()

        # Log action
        action = UserAction(user_id=current_user.id, action_type='clarification', decision_id=decision.id)
        db.session.add(action)
        db.session.commit()

        flash('Clarification request submitted! The owner will review it.')
    return redirect(url_for('main.view_decision', id=id))

@bp.route('/clarification/<int:id>/ignore', methods=['POST'])
@login_required
def ignore_clarification(id):
    clarification = Clarification.query.get_or_404(id)
    if clarification.decision.owner != current_user and not current_user.is_admin:
        abort(403)
    
    clarification.status = 'ignored'
    db.session.commit()
    flash('Clarification request ignored.')
    return redirect(url_for('main.view_decision', id=clarification.decision_id))

@bp.route('/clarification/<int:id>/apply', methods=['POST'])
@login_required
def apply_clarification(id):
    clarification = Clarification.query.get_or_404(id)
    if clarification.decision.owner != current_user and not current_user.is_admin:
        abort(403)
    
    clarification.status = 'applied'
    db.session.commit()
    flash('Clarification request marked as applied!')
    return redirect(url_for('main.view_decision', id=clarification.decision_id))

@bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        abort(403)
    users = User.query.all()
    decisions = Decision.query.all()
    
    # Calculate stats for each user
    user_stats = {}
    for user in users:
        asked = UserAction.query.filter_by(user_id=user.id, action_type='asked').count()
        read = UserAction.query.filter_by(user_id=user.id, action_type='read').count()
        clarifications = UserAction.query.filter_by(user_id=user.id, action_type='clarification').count()
        suggestions = UserAction.query.filter_by(user_id=user.id, action_type='suggestion').count()
        
        # High interaction questions: decisions owned by the user that have many interactions from others
        # OR decisions the user interacted with that are popular? 
        # The user asked: "how many questions had a lot of interaction"
        # Let's count how many of THIS user's questions had > 3 interactions
        high_interaction = 0
        for d in user.decisions:
            interaction_count = UserAction.query.filter(
                UserAction.decision_id == d.id, 
                UserAction.action_type.in_(['suggestion', 'clarification'])
            ).count()
            if interaction_count > 3: # Threshold for "a lot"
                high_interaction += 1
                
        # Top 3 categories
        top_categories = db.session.query(
            Decision.category, db.func.count(UserAction.id).label('count')
        ).join(UserAction, UserAction.decision_id == Decision.id
        ).filter(UserAction.user_id == user.id
        ).group_by(Decision.category
        ).order_by(db.desc('count')
        ).limit(3).all()

        user_stats[user.id] = {
            'asked': asked,
            'read': read,
            'clarifications': clarifications,
            'suggestions': suggestions,
            'high_interaction': high_interaction,
            'top_categories': [cat for cat, count in top_categories if cat]
        }

    return render_template('admin.html', title='Admin', users=users, decisions=decisions, user_stats=user_stats)

@bp.route('/admin/user/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_user(id):
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(id)
    form = EditProfileForm(user.username)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.is_admin = form.is_admin.data
        user.headline = form.headline.data
        user.about = form.about.data
        user.location = form.location.data
        user.experience = form.experience.data
        user.education = form.education.data
        user.skills = form.skills.data
        db.session.commit()
        flash(f'User {user.username} has been updated.')
        return redirect(url_for('main.admin'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.is_admin.data = user.is_admin
        form.headline.data = user.headline
        form.about.data = user.about
        form.location.data = user.location
        form.experience.data = user.experience
        form.education.data = user.education
        form.skills.data = user.skills
    return render_template('edit_profile.html', title='Edit User', form=form, admin_editing=True)

@bp.route('/admin/user/<int:id>/delete', methods=['POST'])
@login_required
def admin_delete_user(id):
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(id)
    if user == current_user:
        flash('You cannot delete yourself!')
        return redirect(url_for('main.admin'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted.')
    return redirect(url_for('main.admin'))

@bp.route('/admin/users/bulk_delete', methods=['POST'])
@login_required
def bulk_delete_users():
    if not current_user.is_admin:
        abort(403)
    
    user_ids = request.form.getlist('user_ids')
    if not user_ids:
        flash('No users selected for deletion.')
        return redirect(url_for('main.admin'))
    
    count = 0
    for u_id in user_ids:
        u_id_int = int(u_id)
        if u_id_int == current_user.id:
            continue
        user = User.query.get(u_id_int)
        if user:
            db.session.delete(user)
            count += 1
    
    if count > 0:
        db.session.commit()
        flash(f'Successfully deleted {count} users.')
    else:
        flash('No users were deleted (you cannot delete yourself via bulk delete).')
        
    return redirect(url_for('main.admin'))

@bp.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        # Regular users cannot change their is_admin status
        current_user.headline = form.headline.data
        current_user.about = form.about.data
        current_user.location = form.location.data
        current_user.experience = form.experience.data
        current_user.education = form.education.data
        current_user.skills = form.skills.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.is_admin.data = current_user.is_admin
        form.headline.data = current_user.headline
        form.about.data = current_user.about
        form.location.data = current_user.location
        form.experience.data = current_user.experience
        form.education.data = current_user.education
        form.skills.data = current_user.skills
    return render_template('edit_profile.html', title='Edit Profile', form=form)
