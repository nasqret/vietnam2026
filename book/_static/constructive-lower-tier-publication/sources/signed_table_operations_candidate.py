"""Actual pointwise arithmetic on finite canonical signed-value tables.

The carrier and lookup graphs are the unchanged packed two-beta ArithTable
and ArithAt relations.  A length l operation witnesses its entries at i<l;
ArithTable(l,F) additionally certifies the harmless unused endpoint i=l.
Neither an output table code nor its positive/negative streams are asserted
unique.  Only their canonical represented values are extensionally unique.
"""

from __future__ import annotations

from typing import Any, Callable

from .divisor_sum_algebra_candidate import _add_code
from .divisor_sum_table_candidate import _pack, _rep, _table, _table_at, _table_equal
from .gaussian_euclidean_candidate import _sd
from .prime_valuation_support_candidate import _and, _call, _cases, _intro, _lt, _part, _parts, _public, _rewrite


def _mul_code(a: str, b: str, c: str, tag: str) -> str:
    ap, an, bp, bn, cp, cn = ('sto_' + role + '_' + tag for role in ('ap', 'an', 'bp', 'bn', 'cp', 'cn'))
    return f'exists {ap} {an} {bp} {bn} {cp} {cn}. ' + _and(
        _sd(a, ap, an, tag + 'left'), _sd(b, bp, bn, tag + 'right'),
        _sd(c, cp, cn, tag + 'output'),
        f'({ap} * {bp} + {an} * {bn}) + {cn} = ({ap} * {bn} + {an} * {bp}) + {cp}')


def _binary_entry(F: str, G: str, H: str, i: str, a: str, b: str, c: str, tag: str, *, multiply: bool) -> str:
    operation = _mul_code if multiply else _add_code
    return _and(_table_at(F, i, a, tag + 'left'), _table_at(G, i, b, tag + 'right'),
                _table_at(H, i, c, tag + 'output'), operation(a, b, c, tag + 'operation'))


def _binary_entries(F: str, G: str, H: str, l: str, tag: str, *, multiply: bool) -> str:
    i, a, b, c = ('sto_' + role + '_' + tag for role in ('index', 'left', 'right', 'output'))
    return f'forall {i}. ({_lt(i,l,tag+"bound")}) -> exists {a} {b} {c}. ' + _binary_entry(F,G,H,i,a,b,c,tag+'entry',multiply=multiply)


def _binary(F: str, G: str, H: str, l: str, tag: str, *, multiply: bool) -> str:
    return _and(_table(l,F,tag+'left_table'), _table(l,G,tag+'right_table'),
                _table(l,H,tag+'output_table'), _binary_entries(F,G,H,l,tag+'entries',multiply=multiply))


def _pointwise_add(F: str, G: str, H: str, l: str, tag: str) -> str:
    return _binary(F,G,H,l,tag,multiply=False)


def _pointwise_multiply(F: str, G: str, H: str, l: str, tag: str) -> str:
    return _binary(F,G,H,l,tag,multiply=True)


def _scalar_entry(a: str, F: str, G: str, i: str, b: str, c: str, tag: str) -> str:
    return _and(_table_at(F,i,b,tag+'input'),_table_at(G,i,c,tag+'output'),_mul_code(a,b,c,tag+'operation'))


def _scalar_entries(a: str, F: str, G: str, l: str, tag: str) -> str:
    i,b,c=('sto_'+role+'_'+tag for role in ('index','input','output'))
    return f'forall {i}. ({_lt(i,l,tag+"bound")}) -> exists {b} {c}. ' + _scalar_entry(a,F,G,i,b,c,tag+'entry')


def _scalar(a: str, F: str, G: str, l: str, tag: str) -> str:
    return _and(_table(l,F,tag+'input_table'),_table(l,G,tag+'output_table'),_scalar_entries(a,F,G,l,tag+'entries'))


def signed_table_pointwise_add_relation(F: str, G: str, H: str, l: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_pointwise_add,(F,G,H,l),tag=tag,variables=variables)


def signed_table_pointwise_multiply_relation(F: str, G: str, H: str, l: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_pointwise_multiply,(F,G,H,l),tag=tag,variables=variables)


def signed_table_scalar_multiply_relation(a: str, F: str, G: str, l: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_scalar,(a,F,G,l),tag=tag,variables=variables)


def _basic_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec('signed_table_domain_resize',
             f"forall N M F. ({_table('N','F','resize_input')}) -> ({_table('M','F','resize_output')})",
             ('divisor_signed_table_components','divisor_signed_table_from_components'),
             _intro('N','M','F','ht')+(f"have hrep : exists pb pc nb nc. ({_rep('F','pb','pc','nb','nc','resize_rep')})",)
             +_call('divisor_signed_table_components','N','F')+('exact ht',)+_cases('hrep',4)
             +_call('divisor_signed_table_from_components','M','F','x','x1','x2','x3')+('exact hrep_witness_witness_witness_witness',),
             'An actual packed beta table has canonical entries on every finite domain; resizing the certificate never changes its streams.'),
        spec('signed_table_lookup_any',
             f"forall N F i. ({_table('N','F','any_lookup_table')}) -> exists z. ({_table_at('F','i','z','any_lookup_result')})",
             ('signed_table_domain_resize','divisor_signed_table_lookup','le_refl'),
             _intro('N','F','i','ht')+_call('divisor_signed_table_lookup','i','F','i')
             +_call('signed_table_domain_resize','N','i','F')+('exact ht',)+_call('le_refl','i'),
             'Every actual table supplies an actual signed value at any requested index, rather than a totality oracle.'),
    )


def _operation_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    rows=[]
    for kind, relation, scalar, multiply in (
        ('add',_pointwise_add,False,False), ('multiply',_pointwise_multiply,False,True),
        ('scalar',_scalar,True,True),
    ):
        symbols=('a','F','G') if scalar else ('F','G','H')
        tables=('F','G') if scalar else ('F','G','H')
        values=('b','c') if scalar else ('a','b','c')
        roots=('x','x1') if scalar else ('x','x1','x2')
        op=_mul_code if multiply else _add_code
        op_args=('a',*values) if scalar else values
        witness_op_args=('a',*roots) if scalar else roots
        count=len(tables)+1
        prefix='signed_table_'+kind
        value_entry=lambda i, vals, tag: (_scalar_entry(*symbols,i,*vals,tag) if scalar else
                                         _binary_entry(*symbols,i,*vals,tag,multiply=multiply))
        entry_formula='exists '+' '.join(values)+'. '+value_entry('i',values,kind+'_lookup_values')
        body=_intro(*symbols,'l','i',*values,'hop','hi',*('h'+str(i) for i in range(len(tables))))
        body+=_parts('hop',count)+(f'have he : {entry_formula}',)
        body+=_call(_part('hop',count,count-1),'i')+('exact hi',)+_cases('he',len(values))+_parts('he'+'_witness'*len(values),count)
        record='he'+'_witness'*len(values)
        for index,(table,source,target) in enumerate(zip(tables,roots,values,strict=True)):
            body+=(f'have heq{index} : {source} = {target}',)
            body+=_call('divisor_signed_table_at_functional',table,'i',source,target)
            body+=(f'exact {_part(record,count,index)}',f'exact h{index}')
            current=list(witness_op_args)
            for before in range(index):
                current[(1 if scalar else 0)+before]=values[before]
            body+=_rewrite(f'heq{index}',op(*current,kind+'_lookup_rewrite'),source,_part(record,count,count-1))
        body+=(f'exact {_part(record,count,count-1)}',)
        statement='forall '+' '.join((*symbols,'l','i',*values))+'. '+f'({relation(*symbols,"l",kind+"_lookup_relation")}) -> ({_lt("i","l",kind+"_lookup_bound")}) -> '
        statement+=' -> '.join('('+_table_at(table,'i',value,kind+'_lookup_'+str(index))+')' for index,(table,value) in enumerate(zip(tables,values,strict=True)))
        statement+=' -> ('+op(*op_args,kind+'_lookup_operation')+')'
        rows.append(spec(prefix+'_lookup',statement,('divisor_signed_table_at_functional',),body,
                         'Every supplied canonical lookup value satisfies the actual '+kind+' graph, by lookup functionality and the witnessed pointwise entries.'))

        body=_intro(*symbols,'l','h')+_parts('h',count)
        for index,table in enumerate(tables):
            body+=('split',)+_call('signed_table_domain_resize','S l','l',table)+(f'exact {_part("h",count,index)}',)
        body+=_intro('i','hi')+_call(_part('h',count,count-1),'i')+_call('le_succ','S i','l')+('exact hi',)
        rows.append(spec(prefix+'_restrict',
                         'forall '+' '.join((*symbols,'l'))+'. '+f'({relation(*symbols,"S l",kind+"_restrict_input")}) -> ({relation(*symbols,"l",kind+"_restrict_output")})',
                         ('signed_table_domain_resize','le_succ'),body,
                         'Restrict the strict pointwise window from S l to l while retaining genuine input and output table certificates.'))

        body=_intro(*symbols,*('ht'+str(i) for i in range(len(tables))))
        for i in range(len(tables)):
            body+=('split',f'exact ht{i}')
        body+=_intro('i','hi')+('cases hi','exfalso')+_call('succ_ne_zero','i')+_call('add_eq_zero_right','x','S i')+('exact hi_witness',)
        rows.append(spec(prefix+'_empty',
                         'forall '+' '.join(symbols)+'. '+' -> '.join('('+_table('0',t,kind+'_empty_'+str(i))+')' for i,t in enumerate(tables))
                         +' -> ('+relation(*symbols,'0',kind+'_empty_result')+')',
                         ('succ_ne_zero','add_eq_zero_right'),body,
                         'The zero-length operation is empty on i<0 but still requires actual packed input and output tables.'))

        other_symbols=('a','F','H') if scalar else ('F','G','K')
        output=tables[-1]
        other_output='H' if scalar else 'K'
        all_symbols=(*symbols,other_output,'l')
        body=_intro(*all_symbols,'hop','hother','i','u','v','hi','hu','hv')
        input_tables=tables[:-1]
        for index,table in enumerate(input_tables):
            body+=(f'have ht{index} : {_table("l",table,kind+"_functional_table"+str(index))}',)
            body+=_parts('hop',count)+(f'exact {_part("hop",count,index)}',)
            body+=(f'have he{index} : exists z. ({_table_at(table,"i","z",kind+"_functional_value"+str(index))})',)
            body+=_call('signed_table_lookup_any','l',table,'i')+(f'exact ht{index}',f'cases he{index}')
        args=('a','x') if scalar else ('x','x1')
        body+=_call('signed_mul_functional' if multiply else 'signed_add_functional',*args,'u','v')
        for graph_symbols,hyp,out in ((symbols,'hop','u'),(other_symbols,'hother','v')):
            decoded=('x',out) if scalar else ('x','x1',out)
            body+=_call(prefix+'_lookup',*graph_symbols,'l','i',*decoded)+(f'exact {hyp}','exact hi')
            body+=tuple(f'exact he{i}_witness' for i in range(len(input_tables)))+(f'exact h{out}',)
        rows.append(spec(prefix+'_extensional_unique',
                         'forall '+' '.join(all_symbols)+'. '+f'({relation(*symbols,"l",kind+"_unique_first")}) -> ({relation(*other_symbols,"l",kind+"_unique_second")}) -> '
                         +f'({_table_equal(output,other_output,"l",kind+"_unique_result")})',
                         ('signed_table_lookup_any',prefix+'_lookup','signed_mul_functional' if multiply else 'signed_add_functional'),body,
                         'Outputs of the same pointwise '+kind+' operation agree in every represented value, not necessarily in their table codes or raw components.'))
    return tuple(rows)


def _construction_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    rows=[]
    for kind,relation,scalar,multiply in (
        ('add',_pointwise_add,False,False),('multiply',_pointwise_multiply,False,True),('scalar',_scalar,True,True),
    ):
        symbols=('a','F','G') if scalar else ('F','G','H')
        input_symbols=symbols[:-1]
        tables=('F','G') if scalar else ('F','G','H')
        input_tables=tables[:-1]
        values=('b','c') if scalar else ('a','b','c')
        output=tables[-1]
        out_symbols=(*symbols[:-1],'K')
        count=len(tables)+1
        prefix='signed_table_'+kind
        op=_mul_code if multiply else _add_code
        op_args=('a',*values) if scalar else values
        entry=lambda syms,i,vals,tag: (_scalar_entry(*syms,i,*vals,tag) if scalar else
                                      _binary_entry(*syms,i,*vals,tag,multiply=multiply))
        generic=('u','v') if scalar else ('u','v','w')
        old_exists='exists '+' '.join(generic)+'. '+entry(symbols,'i',generic,kind+'_extend_old_entry')
        new_exists='exists '+' '.join(generic)+'. '+entry(out_symbols,'i',generic,kind+'_extend_new_entry')
        body=_intro(*symbols,'K','l',*values,'hop','hK','hequal',*('he'+str(i) for i in range(len(tables))),'hvalue')
        body+=_parts('hop',count)
        for index,table in enumerate(input_tables):
            body+=('split',)+_call('signed_table_domain_resize','l','S l',table)+(f'exact {_part("hop",count,index)}',)
        body+=('split',)+_call('signed_table_domain_resize','l','S l','K')+('exact hK',)
        body+=_intro('i','hi')+(f"have hcase : i = l \\/ ({_lt('i','l',kind+'_extend_cases')})",)
        body+=_call('finite_lt_succ_eq_or_lt','l','i')+('exact hi','cases hcase')
        body+=_rewrite('hcase_left',new_exists,'i')+tuple('exists '+value for value in values)
        for index in range(len(tables)):
            body+=('split',f'exact he{index}')
        body+=('exact hvalue',f'have hold : {old_exists}')
        body+=_call(_part('hop',count,count-1),'i')+('exact hcase_right',)+_cases('hold',len(values))+_parts('hold'+'_witness'*len(values),count)
        roots=('x','x1') if scalar else ('x','x1','x2')
        record='hold'+'_witness'*len(values)
        body+=tuple('exists '+value for value in roots)
        for index in range(len(input_tables)):
            body+=('split',f'exact {_part(record,count,index)}')
        body+=('split',)+_call('arithmetic_signed_table_equal_entry_transport','i',output,'K','l','i',roots[-1])
        body+=_call('signed_table_domain_resize','l','i','K')+('exact hK','exact hequal')+_call('le_refl','i')
        body+=('exact hcase_right',f'exact {_part(record,count,len(tables)-1)}',f'exact {_part(record,count,count-1)}')
        statement='forall '+' '.join((*symbols,'K','l',*values))+'. '
        statement+=f'({relation(*symbols,"l",kind+"_extend_source")}) -> ({_table("l","K",kind+"_extend_table")}) -> '
        statement+=f'({_table_equal(output,"K","l",kind+"_extend_preservation")}) -> '
        statement+=' -> '.join('('+_table_at(table,'l',value,kind+'_extend_at_'+str(index))+')'
                               for index,(table,value) in enumerate(zip((*input_tables,'K'),values,strict=True)))
        statement+=f' -> ({op(*op_args,kind+"_extend_operation")}) -> ({relation(*out_symbols,"S l",kind+"_extend_result")})'
        rows.append(spec(prefix+'_extend',statement,
                         ('signed_table_domain_resize','finite_lt_succ_eq_or_lt','arithmetic_signed_table_equal_entry_transport','le_refl'),body,
                         'The actual pointwise '+kind+' graph extends across a preserved strict prefix and a genuine new entry, without equating table codes.'))

        empty_code=_pack('0','0','0','0')
        body=('induction l',)+_intro(*input_symbols,*('ht'+str(i) for i in range(len(input_tables))))
        body+=(f'exists {empty_code}',)+_call(prefix+'_empty',*input_symbols,empty_code)
        body+=tuple('exact ht'+str(i) for i in range(len(input_tables)))
        body+=_call('divisor_signed_table_from_components','0',empty_code,'0','0','0','0')+('refl',)
        body+=_intro(*input_symbols,*('ht'+str(i) for i in range(len(input_tables))))
        body+=(f'have hp : exists K. ({relation(*input_symbols,"K","l",kind+"_construct_prefix")})',)
        body+=_call('IH',*input_symbols)
        for index,table in enumerate(input_tables):
            body+=_call('signed_table_domain_resize','S l','l',table)+(f'exact ht{index}',)
        body+=('cases hp',)
        for index,table in enumerate(input_tables):
            body+=(f'have he{index} : exists z. ({_table_at(table,"l","z",kind+"_construct_input"+str(index))})',)
            body+=_call('signed_table_lookup_any','S l',table,'l')+(f'exact ht{index}',f'cases he{index}')
        root_inputs=('a','x1') if scalar else ('x1','x2')
        result='x2' if scalar else 'x3'
        new_table='x3' if scalar else 'x4'
        body+=(f'have hv : exists z. ({op(*root_inputs,"z",kind+"_construct_operation")})',)
        body+=_call('signed_mul_total' if multiply else 'signed_add_total',*root_inputs)+('cases hv',
              f'have hnext : exists K. {_and(_table("l","K",kind+"_construct_table"),_table_equal("x","K","l",kind+"_construct_equal"),_table_at("K","l",result,kind+"_construct_entry"))}')
        body+=_call('arithmetic_signed_table_extend_at','l','x','l',result)
        body+=_parts('hp_witness',count)+(f'exact {_part("hp_witness",count,len(tables)-1)}',)
        body+=('cases hnext',)+_parts('hnext_witness',3)+(f'exists {new_table}',)
        inputs=('x1',result) if scalar else ('x1','x2',result)
        body+=_call(prefix+'_extend',*input_symbols,'x',new_table,'l',*inputs)
        body+=('exact hp_witness','exact hnext_witness_left','exact hnext_witness_right_left')
        body+=tuple('exact he'+str(i)+'_witness' for i in range(len(input_tables)))
        body+=('exact hnext_witness_right_right','exact hv_witness')
        statement='forall '+' '.join(('l',*input_symbols))+'. '
        statement+=' -> '.join('('+_table('l',table,kind+'_exists_input'+str(index))+')' for index,table in enumerate(input_tables))
        statement+=' -> exists '+output+'. ('+relation(*symbols,'l',kind+'_exists_result')+')'
        rows.append(spec(prefix+'_exists',statement,
                         (prefix+'_empty','divisor_signed_table_from_components','signed_table_domain_resize',
                          'signed_table_lookup_any','signed_mul_total' if multiply else 'signed_add_total',
                          'arithmetic_signed_table_extend_at',prefix+'_extend'),body,
                         'Ordinary finite induction constructs both beta output streams and their actual packed table for pointwise '+kind+'; no finite-choice or supplied-table oracle is used.'))

        body=_intro('l',*input_symbols,*('ht'+str(i) for i in range(len(input_tables))))
        body+=(f'have hw : exists {output}. ({relation(*symbols,"l",kind+"_unique_construct")})',)
        body+=_call(prefix+'_exists','l',*input_symbols)+tuple('exact ht'+str(i) for i in range(len(input_tables)))
        body+=('cases hw','exists x','split','exact hw_witness','intro K','intro hother')
        body+=_call(prefix+'_extensional_unique',*input_symbols,'x','K','l')+('exact hw_witness','exact hother')
        statement='forall '+' '.join(('l',*input_symbols))+'. '
        statement+=' -> '.join('('+_table('l',table,kind+'_exists_unique_input'+str(index))+')' for index,table in enumerate(input_tables))
        statement+=' -> exists '+output+'. '+_and(relation(*symbols,'l',kind+'_exists_unique_result'),
                    f'forall K. ({relation(*input_symbols,"K","l",kind+"_exists_unique_other")}) -> ({_table_equal(output,"K","l",kind+"_exists_unique_equal")})')
        rows.append(spec(prefix+'_exists_extensionally_unique',statement,(prefix+'_exists',prefix+'_extensional_unique'),body,
                         'Construct an actual pointwise '+kind+' output and prove uniqueness of every represented entry; the raw table code is deliberately not claimed unique.'))
    return tuple(rows)


def make_signed_table_operations_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _basic_rows(spec)+_operation_rows(spec)+_construction_rows(spec)


__all__=['signed_table_pointwise_add_relation','signed_table_pointwise_multiply_relation',
         'signed_table_scalar_multiply_relation','make_signed_table_operations_candidate_theorems']
