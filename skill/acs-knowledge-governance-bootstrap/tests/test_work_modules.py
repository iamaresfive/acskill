import copy
import json
import unittest
from unittest.mock import patch
import test_bootstrap as core
b = core.b


class WorkModulesTests(unittest.TestCase):
    setUp = core.BootstrapTests.setUp
    plan = core.BootstrapTests.plan
    run_tool = core.BootstrapTests.run_tool
    def work(self, layout='recommended', **extra):
        return dict({'root':str(self.home/'outputs'), 'layout':layout}, **extra)

    def test_optional_modules_matrix_and_no_external_mutation(self):
        for modules in [[], ['work-files'], ['handoff'], ['work-files', 'handoff']]:
            with self.subTest(modules=modules):
                # Each combination uses its own vault, leaving the other fixtures intact.
                self.v=self.home/('vault-'+str(len(list(self.home.iterdir())))); self.v.mkdir()
                c={'modules':modules}
                if 'work-files' in modules: c['work_files']=self.work()
                if 'handoff' in modules: c['handoff']={'root':str(self.home/'handoff')}
                p=self.plan(config=c,name=self.v.name+'-plan')
                self.assertEqual(list(self.v.iterdir()), [])
                b.apply(p,True)
                self.assertEqual((self.v/'规范与工具/规范/工作文件管理规范.md').exists(), 'work-files' in modules)
                self.assertEqual((self.v/'规范与工具/模板/交接说明.md').exists(), 'handoff' in modules)
                self.assertFalse((self.v/'规范与工具/规范/多Agent协作规范.md').exists())
                self.assertFalse((self.home/'outputs').exists())
                self.assertFalse((self.home/'handoff').exists())
                result=self.run_tool('治理检查.py')
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_existing_and_custom_layout_preserved(self):
        for layout, extra in [('existing',{'instructions':'沿用客户/年份/任务，不改原结构'}),
                              ('custom',{'instructions':'仅两类，不按软件分组','by_software':False,'categories':['研究','制作']})]:
            with self.subTest(layout=layout):
                c=b.config_for(self.v,'new',{'modules':['work-files'],'work_files':self.work(layout,**extra)})
                self.assertEqual(c['work_files']['layout'],layout)
                if layout=='existing': self.assertNotIn('categories',c['work_files'])
                else: self.assertEqual(c['work_files']['categories'],['研究','制作'])
                output=b.render(self.v,'new',c)['规范与工具/规范/工作文件管理规范.md']
                self.assertIn(extra['instructions'],output)

    def test_existing_external_files_are_untouched(self):
        work=self.home/'outputs'; work.mkdir(); (work/'old.txt').write_bytes(b'old task')
        station=work/'handoff'; station.mkdir(); (station/'pending.txt').write_bytes(b'not yet handled')
        before={p.relative_to(work):p.read_bytes() for p in work.rglob('*') if p.is_file()}
        c={'modules':['work-files','handoff'],'work_files':self.work(),'handoff':{'root':str(station)}}
        b.apply(self.plan(config=c),True)
        self.assertEqual({p.relative_to(work):p.read_bytes() for p in work.rglob('*') if p.is_file()},before)

    def test_invalid_options_rejected_before_plan(self):
        invalid=[{'work_files':self.work()}, {'modules':['handoff']},
                 {'modules':['work-files'],'work_files':self.work(root=str(self.v))},
                 {'modules':['work-files'],'work_files':self.work(root='relative')},
                 {'modules':['work-files'],'work_files':self.work(categories=['../escape'])},
                 {'modules':['work-files'],'work_files':self.work(by_software='false')},
                 {'modules':['work-files'],'work_files':self.work('existing')},
                 {'modules':['work-files'],'work_files':self.work('custom',categories=['x'],by_software=False)},
                 {'modules':['handoff'],'handoff':{'root':str(self.home)}},
                 {'modules':['work-files','handoff'],'work_files':self.work(),'handoff':{'root':str(self.home/'outputs')}}]
        for i,c in enumerate(invalid):
            with self.subTest(config=c), self.assertRaises(ValueError): self.plan(config=c,name='bad-'+str(i))
        self.assertEqual(list(self.v.iterdir()),[])

    def test_v12_receipt_additive_upgrade_preserves_sources_and_indexes(self):
        b.apply(self.plan(),True)
        (self.v/'知识/n.md').write_text('# Original knowledge\n')
        (self.v/'索引/知识全量索引.md').write_text('[[知识/n]]\n')
        (self.v/'原始材料/original.txt').write_bytes(b'evidence')
        receipt_path=self.v/'规范与工具/工具/治理安装记录.json'
        receipt=json.loads(receipt_path.read_text()); receipt['version']='1.2.0'
        del receipt['config']['work_files']; del receipt['config']['handoff']
        receipt_path.write_text(json.dumps(receipt))
        originals={p:p.read_bytes() for p in [self.v/'知识/n.md',self.v/'索引/知识全量索引.md',self.v/'原始材料/original.txt']}
        c={'modules':['handoff'],'handoff':{'root':str(self.home/'handoff')}}
        p=self.plan(config=c,name='v13')
        self.assertEqual(json.loads(p.read_text())['added_modules'],['handoff'])
        b.apply(p,True)
        for path,data in originals.items(): self.assertEqual(path.read_bytes(),data)
        repeat=self.plan(config=c,name='repeat')
        self.assertEqual(b.apply(repeat,True)['installed'],0)
        self.assertEqual(self.run_tool('治理检查.py').returncode,0)

    def test_upgrade_keeps_user_edited_rules(self):
        b.apply(self.plan(),True)
        rules=self.v/'规范与工具/规范/知识维护规范.md'; rules.write_text('# User customized rules\n')
        p=self.plan(config={'modules':['handoff'],'handoff':{'root':str(self.home/'handoff')}},name='upgrade')
        with self.assertRaises(ValueError): b.apply(p,True)
        self.assertEqual(rules.read_text(),'# User customized rules\n')
        self.assertFalse((self.v/'规范与工具/规范/交接中转站规范.md').exists())

    def test_removal_or_path_change_needs_separate_plan(self):
        c={'modules':['work-files'],'work_files':self.work()}
        b.apply(self.plan(config=c),True)
        with self.assertRaises(ValueError): self.plan(config={},name='remove')
        changed=copy.deepcopy(c); changed['work_files']['root']=str(self.home/'other')
        with self.assertRaises(ValueError): self.plan(config=changed,name='relocate')
        self.assertFalse((self.home/'other').exists())

    def test_new_module_failure_rolls_back_and_preserves_existing_work(self):
        b.apply(self.plan(),True)
        before={p.relative_to(self.v):p.read_bytes() for p in self.v.rglob('*') if p.is_file()}
        p=self.plan(config={'modules':['handoff'],'handoff':{'root':str(self.home/'handoff')}},name='upgrade')
        atomic=b.atomic; count=[0]
        def fail(path,data):
            count[0]+=1
            if count[0]==3: raise OSError('simulated failure')
            return atomic(path,data)
        with patch.object(b,'atomic',fail), self.assertRaises(OSError): b.apply(p,True)
        self.assertEqual({p.relative_to(self.v):p.read_bytes() for p in self.v.rglob('*') if p.is_file()},before)
        self.assertFalse((self.home/'handoff').exists())
