"""Small, synthetic, source-free contracts shared by procbench tests."""


def observation(ident,basis,lower,upper,case='c',activities=None):
    operator=dict(basis=basis)
    if activities:
        operator['activity_ids']=activities
    if basis=='whole_case_clock':
        operator.update(start='process_start',end='initial_decision')
    return dict(id=ident,case_id=case,source_family='source',sampling='unselected',
        statistic='individual' if case else 'median',lower=lower,upper=upper,
        operators=[operator],operator_weights=[1.])


def data_fixture():
    return dict(programs=[dict(id='J__P',routes=[dict(id='simple',prior_weight=1.,operations=[
        dict(id='file',actor_id='payer',actor_role='payer',task_type='filing',markers=['submission'],
             payer_work=True,agency_work=False),
        dict(id='review',actor_id='J:Review',actor_role='agency',task_type='review',
             payer_work=False,agency_work=True),
        dict(id='decide',actor_id='J:Review',actor_role='agency',task_type='decision',markers=['decision'],
             payer_work=False,agency_work=True)],blocks=[
        dict(id='loop',operations=['file','review'],repeat_key='corrections'),
        dict(id='end',operations=['decide'])])],observations=[
            observation('total','whole_case_clock',15.,25.),
            observation('task','single_visit_cycle',4.,10.,activities=['review']),
            observation('visits','visit_count',3,3),
            observation('labor','agency_hours',1.,3.)],rate_observations=[])])
