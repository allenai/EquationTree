'''
Created on Dec 14, 2014

@author: minjoon
'''
from pyparsing import Word, nums, Optional, OneOrMore, alphas, alphanums, \
    Forward, Literal, ZeroOrMore
import tempfile

import cv2

import networkx as nx

class EquationTreeParser(object):
    cfg_string = '''
    expr -> form0 comp form0 | form0
    comp -> '>'|'<'|'='|'<='|'>='
    form0 -> form0 op1 form1> | form1>
    op1 -> '+'|'-'
    form1 -> form1 op2 form2 | neg form1 | form2
    op2 -> '*'|'/'
    neg -> '-'
    form2 -> form2 op3 form3 | form3
    op3 -> '^'
    form3 -> '(' expr ')' | symbol '(' expr ')' | value
    value -> const | symbol
    symbol -> [_\w][_\w\d]*
    const -> (\d)+ | (\d)*.\d*
    '''
    operators = list('+-*/^=<>') + ['<=', '>=']
    
    def __init__(self):
        self._stack = []
        self._function_indices = []
        self.parser = EquationTreeParser.get_parser(self._stack,
                                                    self._function_indices)
    
    @staticmethod
    def get_parser(stack, function_indices):
        '''
        Helper function for init.
        If you change anything here, please change the cfg string as well.
        Add negation functionality later
        '''
        def _push(str_, loc, toks):
            stack.append(toks[0]) 
        def _push_func(str_, loc, toks):
            function_indices.append(len(stack))
            stack.append(toks[0])
        
        number = Word(nums) + Optional("." + OneOrMore(Word(nums))) 
        symbol = Word(alphas+"_", alphanums+"_")
        const = (number | symbol).setParseAction(_push)
        expr = Forward()
        paren = Literal('(').suppress() + expr + Literal(')').suppress()
        atom = (symbol + paren).setParseAction(_push_func) | paren | const
        op3 = Literal('^')
        factor = atom + ZeroOrMore((op3 + atom).setParseAction(_push))
        neg = Literal('-')
        literal = (neg + factor).setParseAction(_push_func) | factor
        multop = Word('*/', max=1)
        term = literal + ZeroOrMore((multop + literal).setParseAction(_push))
        addop = Word('+-', max=1)
        expr << term + ZeroOrMore((addop + term).setParseAction(_push))
        comp = Literal('>=') | Literal('<=') | Word('><=', max=1) 
        bnf = expr + Optional((comp + expr).setParseAction(_push))
        
        return bnf
        
    def parse(self, string):
        '''
        Returns postfix notation in an array
        '''
        del self._stack[:]
        del self._function_indices[:]
        parsed = self.parser.parseString(string)
        return (self._stack, self._function_indices)
    
    @staticmethod
    def _create_tree(stack, indices, explicit=False):
        '''
        Create networkx DiGraph using postfix notation stack.
        Non-destructive (i.e. copies stack)
        '''
        stack = stack[:]
        tree = nx.DiGraph()
        node_idx = 0
        tree.add_node(node_idx, label='ROOT')
        jobs = []
        jobs.append((0,""))
        while len(jobs) > 0:
            idx,direc = jobs.pop()
            token = stack.pop()
            node_idx += 1
            tree.add_node(node_idx, label=token)
            tree.add_edge(idx, node_idx, label=direc)
            if len(stack) in indices:
                jobs.append((node_idx,'')) 
            elif token in EquationTreeParser.operators:
                jobs.append((node_idx,'left'))
                jobs.append((node_idx,'right')) 
            
        return tree
        
    def parse_tree(self, string, explicit=False, display=False):
        '''
        Returns graph representation of the equation tree of string,
        as a networkx graph. 
        If explicit is True, then '-x' -> '0-x'
        '''
        stack, indices = self.parse(string)
        tree = EquationTreeParser._create_tree(stack, indices)
       
        if explicit:
            idx = -1
            for node, data in tree.nodes(data=True):
                if data['label'] == '-' and len(tree[node]) == 1:
                    nbr = tree[node].keys()[0]
                    tree.remove_edge(node, nbr)
                    tree.add_node(idx, label='0')
                    tree.add_edge(node, idx, label='left')
                    tree.add_edge(node, nbr, label='right')
                    idx -= 1
        
        if display:
            _, image_path = tempfile.mkstemp()
            pydot_graph = nx.to_pydot(tree)
            pydot_graph.write_png(image_path)
            cv2.imshow('equation tree', cv2.imread(image_path))
            cv2.waitKey()
            cv2.destroyAllWindows()
            
        return tree
    
    def parse_formula(self, string, explicit=False):
        '''
        returns prefix notation formula by default
        '''
        tree = self.parse_tree(string,explicit=explicit)
        
        def recurse(idx):
            label = tree.node[idx]['label']
            edges = tree.edges(idx)
            if len(edges) == 0:
                return label
            out = []
            for _, child in edges:
                out.append(recurse(child))
            out.append(label)
            out.reverse()
            return out
                
        return recurse(1)
                
etp = EquationTreeParser()
        
        
if __name__ == "__main__":
    string = "-x=5+z"
    tree = etp.parse_tree(string,explicit=True,display=True)
    formula = etp.parse_formula(string,explicit=True)
    print(formula)
    